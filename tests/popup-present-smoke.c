/* SPDX-License-Identifier: MIT
 * Integration probe for a private X server, or an idle test workspace.
 * Creates and destroys only its own small override-redirect windows. No input.
 */
#define _GNU_SOURCE
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/extensions/Xrender.h>
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static Display *d;
static Window make(unsigned long style, unsigned long ex)
{
    XSetWindowAttributes a = {.override_redirect = True, .background_pixel = 0};
    Window w = XCreateWindow(d, DefaultRootWindow(d), DisplayWidth(d, DefaultScreen(d))-100, DisplayHeight(d, DefaultScreen(d))-80, 80, 60, 0,
        24, InputOutput, DefaultVisual(d, DefaultScreen(d)), CWOverrideRedirect | CWBackPixel, &a);
    XChangeProperty(d, w, XInternAtom(d, "_WINE_HWND_STYLE", False), XA_CARDINAL, 32,
        PropModeReplace, (unsigned char *)&style, 1);
    XChangeProperty(d, w, XInternAtom(d, "_WINE_HWND_EXSTYLE", False), XA_CARDINAL, 32,
        PropModeReplace, (unsigned char *)&ex, 1);
    return w;
}
static int state(Window w) { XWindowAttributes a; XGetWindowAttributes(d, w, &a); return a.map_state; }
int main(void)
{
    XInitThreads();
    d = XOpenDisplay(NULL); assert(d);
    void *r = dlopen("libXrender.so.1", RTLD_NOW | RTLD_LOCAL); assert(r);
    XRenderPictFormat *(*format)(Display *, const Visual *) = dlsym(r, "XRenderFindVisualFormat");
    Picture (*create)(Display *, Drawable, const XRenderPictFormat *, unsigned long, const XRenderPictureAttributes *) = dlsym(r, "XRenderCreatePicture");
    void (*composite)(Display *, int, Picture, Picture, Picture, int, int, int, int, int, int, unsigned, unsigned) = dlsym(r, "XRenderComposite");
    void (*release)(Display *, Picture) = dlsym(r, "XRenderFreePicture");
    XRenderPictFormat *f = format(d, DefaultVisual(d, DefaultScreen(d)));
    for (int i = 0; i < 80; i++) {
        Window w = make(0x96000000, 0x88);
        XMapWindow(d, w); assert(state(w) == IsUnmapped);
        Pixmap p = XCreatePixmap(d, w, 80, 60, 24);
        GC gc = XCreateGC(d, p, 0, NULL);
        unsigned long color = 0x55bb99;
        XSetForeground(d, gc, color); XFillRectangle(d, p, gc, 0, 0, 80, 60);
        Picture src = create(d, p, f, 0, NULL), dst = create(d, w, f, 0, NULL);
        composite(d, PictOpSrc, src, 0, dst, 0, 0, 0, 0, 0, 0, 80, 60);
        assert(state(w) == IsViewable);
        XImage *image = XGetImage(d, w, 0, 0, 80, 60, AllPlanes, ZPixmap); assert(image);
        assert((XGetPixel(image, 40, 30) & 0xffffff) == color);
        XDestroyImage(image); release(d, src); release(d, dst);
        XFreeGC(d, gc); XFreePixmap(d, p); XDestroyWindow(d, w);
    }
    Window w = make(0x96000000, 0x88);
    XMapWindow(d, w); assert(state(w) == IsUnmapped);
    usleep(350000); assert(state(w) == IsViewable); XDestroyWindow(d, w);
    w = make(0x96000000, 0x88); XMapWindow(d, w); XUnmapWindow(d, w);
    usleep(350000); assert(state(w) == IsUnmapped); XDestroyWindow(d, w);
    w = make(0x96000000, 0x88); XMapWindow(d, w); XDestroyWindow(d, w); XSync(d, False);
    usleep(350000); /* destroy before paint must not map a stale window */
    w = make(0x96c00000, 0x88); XMapWindow(d, w); assert(state(w) == IsViewable); XDestroyWindow(d, w);
    w = make(0x96000000, 0x80088); XMapWindow(d, w); assert(state(w) == IsViewable); XDestroyWindow(d, w);
    /* Owned dialog background initializes white; the model-like owner stays black. */
    setenv("AAG_DIALOG_BACKGROUND", "white", 1);
    Window owner = make(0x96c00000, 0x100);
    XMapWindow(d, owner);
    XImage *owner_image = XGetImage(d, owner, 0, 0, 80, 60, AllPlanes, ZPixmap);
    assert(owner_image && (XGetPixel(owner_image, 40, 30) & 0xffffff) == 0);
    XDestroyImage(owner_image);
    w = make(0x96c00000, 0x100);
    XSetTransientForHint(d, w, owner);
    Atom dialog_type = XInternAtom(d, "_NET_WM_WINDOW_TYPE_DIALOG", False);
    XChangeProperty(d, w, XInternAtom(d, "_NET_WM_WINDOW_TYPE", False), XA_ATOM, 32,
        PropModeReplace, (unsigned char *)&dialog_type, 1);
    XMapWindow(d, w);
    XImage *dialog_image = XGetImage(d, w, 0, 0, 80, 60, AllPlanes, ZPixmap);
    assert(dialog_image && (XGetPixel(dialog_image, 40, 30) & 0xffffff) == 0xffffff);
    XDestroyImage(dialog_image); XDestroyWindow(d, w);
    w = make(0x94000000, 8); XSetTransientForHint(d, w, owner);
    XChangeProperty(d, w, XInternAtom(d, "_NET_WM_WINDOW_TYPE", False), XA_ATOM, 32,
        PropModeReplace, (unsigned char *)&dialog_type, 1);
    XMapWindow(d, w); assert(state(w) == IsViewable);
    dialog_image = XGetImage(d, w, 0, 0, 80, 60, AllPlanes, ZPixmap);
    assert(dialog_image && (XGetPixel(dialog_image, 40, 30) & 0xffffff) == 0xffffff);
    XDestroyImage(dialog_image); XDestroyWindow(d, w); XDestroyWindow(d, owner);
    setenv("WINEPREFIX", "/different-prefix", 1);
    w = make(0x96000000, 0x88); XMapWindow(d, w); assert(state(w) == IsViewable); XDestroyWindow(d, w);
    XSync(d, False);
    puts("PASS: 80 buffered first paints; timeout; unmap/destroy cancellation; caption/layered/prefix exclusions; owned-dialog background; model background unchanged");
    return 0;
}
