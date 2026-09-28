/* SPDX-License-Identifier: MIT
 * AAG: prepare Wine raster tool-popups before their first X11 map.
 * Original support source. No SketchUp or Wine binary/source is embedded here.
 * Opt-in, prefix-scoped, X11-only. Validated environment belongs in the manifest.
 * This does not hook OpenGL, change focus, or change compositor policy.
 */
#define _GNU_SOURCE
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/extensions/Xrender.h>
#include <xcb/xcb.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define MAX_PENDING 64
#define FALLBACK_NS 250000000L
struct pending {
    Window window;
    unsigned width, height, depth;
    bool active;
    struct timespec deadline;
};
struct picture {
    Picture id;
    Drawable drawable;
    XRenderPictFormat format;
    struct picture *next;
};
typedef void *(*lookup_fn)(void *, const char *);
typedef Picture (*create_fn)(Display *, Drawable, const XRenderPictFormat *,
                             unsigned long, const XRenderPictureAttributes *);
typedef void (*composite_fn)(Display *, int, Picture, Picture, Picture,
                             int, int, int, int, int, int, unsigned, unsigned);
typedef void (*free_fn)(Display *, Picture);
static _Atomic(create_fn) real_create;
static _Atomic(composite_fn) real_composite;
static _Atomic(free_fn) real_free;
static struct pending pending[MAX_PENDING];
static struct picture *pictures;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed;
static pthread_once_t initialize_once = PTHREAD_ONCE_INIT;
static xcb_connection_t *fallback_connection;
static bool ready;

static void *lookup(void *handle, const char *name)
{
    lookup_fn fn = (lookup_fn)dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.2.5");
    return fn ? fn(handle, name) : NULL;
}
static bool enabled(void)
{
    const char *flag = getenv("AAG_POPUP_PRESENT");
    const char *expected = getenv("AAG_POPUP_PREFIX");
    const char *actual = getenv("WINEPREFIX");
    if (!flag || strcmp(flag, "1") || !expected || !actual || *expected != '/' || *actual != '/') return false;
    size_t ne = strlen(expected), na = strlen(actual);
    while (ne > 1 && expected[ne - 1] == '/') ne--;
    while (na > 1 && actual[na - 1] == '/') na--;
    return ne == na && !memcmp(expected, actual, ne);
}
static struct timespec monotonic_now(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t;
}
static int compare(struct timespec a, struct timespec b)
{
    if (a.tv_sec != b.tv_sec) return a.tv_sec < b.tv_sec ? -1 : 1;
    return (a.tv_nsec > b.tv_nsec) - (a.tv_nsec < b.tv_nsec);
}
static void trace(const char *event, Window window, unsigned width, unsigned height)
{
    const char *path = getenv("AAG_POPUP_TRACE");
    if (!path || !*path) return;
    FILE *f = fopen(path, "a");
    if (!f) return;
    struct timespec t = monotonic_now();
    fprintf(f, "%lld.%09ld pid=%d window=0x%lx event=%s width=%u height=%u\n",
            (long long)t.tv_sec, t.tv_nsec, getpid(), window, event, width, height);
    fclose(f);
}
static struct pending *find_pending(Window window)
{
    for (unsigned i = 0; i < MAX_PENDING; i++)
        if (pending[i].active && pending[i].window == window) return &pending[i];
    return NULL;
}
/* A separate XCB connection gives timeout requests checked errors. A window
 * destroyed in the meantime must not trigger Xlib's process-fatal handler.
 * No polling when idle and no additional process/service is started.
 */
static void *fallback_worker(void *unused)
{
    (void)unused;
    pthread_mutex_lock(&mutex);
    for (;;) {
        struct pending *first = NULL;
        for (unsigned i = 0; i < MAX_PENDING; i++)
            if (pending[i].active && (!first || compare(pending[i].deadline, first->deadline) < 0))
                first = &pending[i];
        if (!first) { pthread_cond_wait(&changed, &mutex); continue; }
        if (compare(monotonic_now(), first->deadline) < 0) {
            pthread_cond_timedwait(&changed, &mutex, &first->deadline);
            continue;
        }
        xcb_generic_error_t *err = xcb_request_check(fallback_connection,
            xcb_map_window_checked(fallback_connection, (xcb_window_t)first->window));
        trace(err ? "fallback-window-gone" : "fallback-timeout", first->window,
              first->width, first->height);
        free(err);
        first->active = false;
    }
    return NULL;
}
static void initialize(void)
{
    pthread_condattr_t attr;
    pthread_condattr_init(&attr);
    pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
    pthread_cond_init(&changed, &attr);
    pthread_condattr_destroy(&attr);
    fallback_connection = xcb_connect(NULL, NULL);
    if (!fallback_connection || xcb_connection_has_error(fallback_connection)) {
        if (fallback_connection) xcb_disconnect(fallback_connection);
        fallback_connection = NULL;
        return;
    }
    pthread_t worker;
    if (pthread_create(&worker, NULL, fallback_worker, NULL)) {
        xcb_disconnect(fallback_connection);
        fallback_connection = NULL;
        return;
    }
    pthread_detach(worker);
    ready = true;
}
static unsigned long property(Display *d, Window w, const char *name)
{
    Atom atom = XInternAtom(d, name, True), type;
    int format;
    unsigned long count, left, value = 0;
    unsigned char *data = NULL;
    if (atom && XGetWindowProperty(d, w, atom, 0, 1, False, XA_CARDINAL,
            &type, &format, &count, &left, &data) == Success &&
            type == XA_CARDINAL && data && format == 32 && count == 1)
        value = *(unsigned long *)data;
    if (data) XFree(data);
    return value & 0xffffffffUL; /* Xlib format-32 values can be sign-extended on LP64. */
}
static int map_now(Display *d, Window w)
{
    int (*fn)(Display *, Window) = lookup(RTLD_NEXT, "XMapWindow");
    return fn(d, w);
}
int XMapWindow(Display *d, Window w)
{
    if (!enabled()) return map_now(d, w);
    unsigned long style = property(d, w, "_WINE_HWND_STYLE");
    unsigned long exstyle = property(d, w, "_WINE_HWND_EXSTYLE");
    if (getenv("AAG_POPUP_TRACE")) { char info[96]; snprintf(info, sizeof info, "map-style-%lx-ex-%lx", style, exstyle); trace(info, w, 0, 0); }
    /* In the validated light UI, Wine's default black X11 background becomes
     * visible while a newly mapped owned HTML dialog waits for CEF's first
     * content paint. Initialize that background without erasing later content.
     * The model window has no transient owner and is never affected.
     */
    const char *background = getenv("AAG_DIALOG_BACKGROUND");
    bool native_menu = style == 0x94000000UL && exstyle == 8;
    if (background && !strcmp(background, "white") && ((style & 0x00c00000UL) || native_menu) && !(exstyle & 0x80000UL)) {
        Window owner;
        if (XGetTransientForHint(d, w, &owner) && owner && property(d, owner, "_WINE_HWND_STYLE")) {
            Atom kind = XInternAtom(d, "_NET_WM_WINDOW_TYPE", True), type;
            Atom dialog = XInternAtom(d, "_NET_WM_WINDOW_TYPE_DIALOG", True);
            int format; unsigned long count, left; unsigned char *data = NULL;
            if (kind && dialog && XGetWindowProperty(d, w, kind, 0, 16, False, XA_ATOM,
                    &type, &format, &count, &left, &data) == Success && data && type == XA_ATOM && format == 32) {
                for (unsigned long i = 0; i < count; i++) if (((Atom *)data)[i] == dialog) {
                    XSetWindowBackground(d, w, 0xffffff);
                    trace(native_menu ? "initialize-native-menu-background" : "initialize-dialog-background", w, 0, 0);
                    break;
                }
            }
            if (data) XFree(data);
        }
    }
    /* WS_POPUP, no caption, exactly WS_EX_TOPMOST | WS_EX_TOOLWINDOW.
     * Excludes ordinary dialogs, model windows and WS_EX_LAYERED surfaces.
     */
    if (!(style & 0x80000000UL) || (style & 0x00c00000UL) || exstyle != 0x88)
        return map_now(d, w);
    XWindowAttributes a;
    if (!XGetWindowAttributes(d, w, &a) || !a.override_redirect || a.map_state != IsUnmapped ||
        a.depth != 24 || a.width < 8 || a.height < 8 || a.width > 4096 || a.height > 4096)
        return map_now(d, w);
    pthread_once(&initialize_once, initialize);
    if (!ready) return map_now(d, w);
    pthread_mutex_lock(&mutex);
    struct pending *p = find_pending(w);
    if (!p) for (unsigned i = 0; i < MAX_PENDING; i++) if (!pending[i].active) { p = &pending[i]; break; }
    if (p) {
        *p = (struct pending){w, (unsigned)a.width, (unsigned)a.height, (unsigned)a.depth, true, monotonic_now()};
        p->deadline.tv_nsec += FALLBACK_NS;
        if (p->deadline.tv_nsec >= 1000000000L) { p->deadline.tv_sec++; p->deadline.tv_nsec -= 1000000000L; }
        trace("defer-map", w, p->width, p->height);
        pthread_cond_signal(&changed);
    }
    pthread_mutex_unlock(&mutex);
    return p ? 1 : map_now(d, w);
}
static void cancel_pending(Window w)
{
    pthread_mutex_lock(&mutex);
    struct pending *p = find_pending(w);
    if (p) { p->active = false; trace("cancel-before-paint", w, p->width, p->height); }
    pthread_mutex_unlock(&mutex);
}
int XUnmapWindow(Display *d, Window w)
{
    cancel_pending(w);
    int (*fn)(Display *, Window) = lookup(RTLD_NEXT, "XUnmapWindow");
    return fn(d, w);
}
int XDestroyWindow(Display *d, Window w)
{
    cancel_pending(w);
    int (*fn)(Display *, Window) = lookup(RTLD_NEXT, "XDestroyWindow");
    return fn(d, w);
}
static Picture create_picture(Display *d, Drawable draw, const XRenderPictFormat *format,
                              unsigned long mask, const XRenderPictureAttributes *attrs)
{
    Picture id = atomic_load(&real_create)(d, draw, format, mask, attrs);
    struct picture *p = malloc(sizeof *p);
    if (p) {
        *p = (struct picture){id, draw, *format, NULL};
        pthread_mutex_lock(&mutex);
        p->next = pictures; pictures = p;
        pthread_mutex_unlock(&mutex);
    }
    return id;
}
static void free_picture(Display *d, Picture id)
{
    pthread_mutex_lock(&mutex);
    for (struct picture **p = &pictures; *p; p = &(*p)->next) if ((*p)->id == id) {
        struct picture *old = *p; *p = old->next; free(old); break;
    }
    pthread_mutex_unlock(&mutex);
    atomic_load(&real_free)(d, id);
}
static void composite(Display *d, int op, Picture src, Picture mask, Picture dst,
                      int sx, int sy, int mx, int my, int dx, int dy, unsigned width, unsigned height)
{
    pthread_mutex_lock(&mutex);
    struct picture *pic;
    for (pic = pictures; pic && pic->id != dst; pic = pic->next) {}
    struct pending *p = pic ? find_pending(pic->drawable) : NULL;
    if (!p) {
        pthread_mutex_unlock(&mutex);
        atomic_load(&real_composite)(d, op, src, mask, dst, sx, sy, mx, my, dx, dy, width, height);
        return;
    }
    p->active = false;
    if (op == PictOpSrc && !mask && dx == 0 && dy == 0 && width == p->width &&
        height == p->height && pic->format.depth == (int)p->depth && atomic_load(&real_free)) {
        Pixmap pixmap = XCreatePixmap(d, p->window, width, height, p->depth);
        Picture buffer = atomic_load(&real_create)(d, pixmap, &pic->format, 0, NULL);
        atomic_load(&real_composite)(d, op, src, mask, buffer, sx, sy, mx, my, dx, dy, width, height);
        /* X requests on this connection execute in order. Initial map paints
         * the completed background; no blank mapped window precedes it.
         */
        XSetWindowBackgroundPixmap(d, p->window, pixmap);
        map_now(d, p->window);
        XSetWindowBackground(d, p->window, 0); /* Wine's original background pixel. */
        atomic_load(&real_free)(d, buffer);
        XFreePixmap(d, pixmap);
        XFlush(d);
        trace("map-painted-buffer", p->window, width, height);
    } else {
        /* Unknown drawing route: keep the window usable and record the limit. */
        map_now(d, p->window);
        atomic_load(&real_composite)(d, op, src, mask, dst, sx, sy, mx, my, dx, dy, width, height);
        XFlush(d);
        trace("fallback-unrecognized-paint", p->window, width, height);
    }
    pthread_mutex_unlock(&mutex);
}
/* Wine loads XRender with dlsym(handle,...), so ordinary symbol interposition
 * alone does not cover its drawing calls. Every other lookup passes through.
 */
void *dlsym(void *handle, const char *name)
{
    void *p = lookup(handle, name);
    if (!p || !enabled()) return p;
    if (!strcmp(name, "XRenderCreatePicture")) {
        atomic_store(&real_create, (create_fn)p);
        atomic_store(&real_free, (free_fn)lookup(handle, "XRenderFreePicture"));
        return create_picture;
    }
    if (!strcmp(name, "XRenderFreePicture")) { atomic_store(&real_free, (free_fn)p); return free_picture; }
    if (!strcmp(name, "XRenderComposite")) { atomic_store(&real_composite, (composite_fn)p); return composite; }
    return p;
}
