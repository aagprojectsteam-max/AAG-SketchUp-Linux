# Secure networking in the private runtime

Status: **core networking/account regression passed on 2026-09-29** for the recorded SketchUp 26.1.252 / GE-Proton10-25 / sniper configuration. Base and Plugin Golden backups and historical tags are preserved. This is a support-code maintenance change, not an application upgrade. Optional service results and a failed diagnostic experiment are recorded below.

## Root cause established by comparison

The Ubuntu host could resolve and validate HTTPS. The same requests inside the actual sniper runtime resolved normally but failed certificate-chain validation on sites inspected by the host's network filter. The inherited `SSL_CERT_FILE` named a host path absent inside the container. Stock public roots still allowed some other sites to work.

Copying the existing host CA bundle into the private installation and referencing it from the container resolved the failures. A separately compiled Windows probe also changed from failed WinHTTP/WinINet HTTPS requests to successful requests. No DNS, firewall, filtering or TLS verification setting was weakened.

This comparison identifies a trust-store integration problem. An HTTP 403 from a service root is an HTTP response, not evidence of failed DNS or TLS.

## Implementation

`bin/network-environment.py` reads the host's existing `SSL_CERT_FILE`, or OpenSSL's system CA file when unset. At launch it validates the PEM, rejects private keys and oversized inputs, and refreshes a private copy under `config/network/`. Generated files use mode 0600 and the directory uses 0700. Output symlinks and directory escapes are rejected.

The launcher supplies the copy through `SSL_CERT_FILE`, `CURL_CA_BUNDLE`, `REQUESTS_CA_BUNDLE` and Wine's `WINE_ADDITIONAL_CERTS_DIR`. The last variable is supported by the exact validated GE Wine source. Wine synchronizes host-imported certificates while retaining independently added prefix certificates. This does not download certificates or trust arbitrary servers.

SketchUp also resets Ruby's `SSL_CERT_FILE` to its own `Tools/cacert.pem` during startup. A second controlled comparison established that its embedded Ruby/OpenSSL still rejected the filtered chain after the container and Windows APIs were fixed. The original prefix-local `000_AAG_HostTrust.rb` bootstrap checks the launch-supplied host bundle hash, gives future Ruby stores the correct Windows path, and adds those roots to OpenSSL's already-created default store. It preserves peer verification, hostname checks and store flags. It does not modify vendor Ruby code or the vendor CA file. A cold launch confirmed the bootstrap loaded and an unmodified `Net::HTTP` HTTPS request succeeded.

The installer and update-candidate preparation copy this helper. A different future runtime still needs its own Windows API, CEF and Ruby checks; an environment variable alone does not establish compatibility.

Existing proxy environment values are inherited. Existing `NO_PROXY` entries are retained and loopback names are added. The validated host uses direct connections and no desktop proxy. PAC, authenticated proxies and every third-party plugin's private HTTP stack are not certified by this test. Proxy values are omitted from launch receipts.

The CA bundle is refreshed when SketchUp launches. Restart SketchUp after changing host trust. No private bundle, certificate, account state, prefix or compiled probe belongs in the public repository.

## Browser and callback

The existing Wine HTTP/HTTPS association uses `winebrowser.exe`. Its default first candidate is `xdg-open`, and the URL is passed as a separate argument to process spawning. The existing bridge opened the normal Ubuntu browser successfully; no replacement browser, custom browser script or global association change was required.

The observed SketchUp 26.1.252 flow started at the Welcome account icon. A listener appeared on IPv4 loopback at an ephemeral port, the browser showed SketchUp's successful sign-in page at that loopback address, and SketchUp's own account indicator changed to connected. The listener was no longer present after completion. No custom protocol handler was required. Credentials and authorization parameters were neither copied nor recorded. The user confirmed the account before further tests.

Cold launches from GNOME Apps and the pinned Dock icon both retained the connected account indicator. This proves persistence across those launches, not indefinite session lifetime.

## Current evidence

| Layer / check | Result |
| --- | --- |
| Host DNS, TCP, TLS and HTTPS | Pass on multiple public endpoints |
| Container DNS and shared host network namespace | Pass |
| Container HTTPS with existing host trust | Pass on seven tested endpoints |
| Wine Winsock DNS, WinHTTP and WinINet HTTPS | Pass on the controlled public test |
| Untrusted local HTTPS certificate | Rejected by host, container, WinHTTP and WinINet |
| Actual browser callback and SketchUp account indicator | Pass |
| Apps and Dock session persistence | Pass |
| Ruby, SketchUp HTTP API and CEF HTTPS | Pass; Ruby also verified after a cold launch |
| Extension Warehouse | Connected account and real search results; no extension installed |
| 3D Warehouse | Real search results and thumbnails; no model downloaded |
| SketchUcation ExtensionStore | Online login page rendered; optional account login deferred |
| Add Location | Real address-search suggestions returned; map rendering unavailable because WebGL initialization fails |
| Trimble Connect | Account recognized; separate first-use terms still presented. USER_ACTION_DEFERRED under the user's optional-service instruction; full project access not verified |
| Generate Report | Existing host filtering-policy block rendered; no bypass or report generation |
| PreDesign | Loading did not complete after more than 90 seconds; feature not validated, cause not established |
| AI Assistant / AI Render | Not tested: no generation, model upload or paid-credit operation performed |
| Collaboration | Deferred with Connect onboarding |
| Final GUI regression and cleanup | Three cold runs passed; each normal close left zero prefix processes; no new dump or fatal X error in those runs |
| DPI / MSAA / hardware | 192 / 8x / actual renderD128 use preserved; 19 critical binary hashes unchanged |
| Painting / pointer / window controls | Recorded menus, toolbar popup, plugin first paint/focus, model selection and native maximize/restore passed |

The controlled negative TLS test was also repeated through Ruby, which rejected the untrusted self-signed certificate. The local HTTP browser bridge received the exact expected path, query parameters and percent-encoded punctuation. A separate HTTPS URL with query parameters and percent-encoded punctuation was also visually verified in the normal default browser. The test servers stopped and their listeners were absent afterward.

An instrumented test that combined a background Ruby thread and an HtmlDialog ended with an X11 `BadMatch` on `X_CopyArea` while closing the dialog. Its cause is not established; it is not hidden by the service exit code, which was zero. Subsequent built-in service dialogs closed normally. Three subsequent controlled HtmlDialog open/close cycles passed without that error after using a probe with no background Ruby thread. This does not establish the original error's cause; the failed run remains in the record. The final three cold runs subsequently passed without a fatal X error, unhandled-exception signature or new crash dump. The first remained alive for more than six hours (mostly idle); the Apps run lasted about five minutes and the Dock run 259 seconds before normal close. These observations do not establish the earlier failure's cause or guarantee indefinite stability. No production painting or GPU setting was changed.

Private receipts retain timestamps, safe status fields and local evidence references. They do not contain authentication codes or session tokens.

## Troubleshooting by layer

1. Check normal host HTTPS first. A host policy block must remain a policy block.
2. Compare DNS, TCP, TLS and HTTP status separately in the actual runtime.
3. Confirm the generated CA file exists inside the container and the launch uses it.
4. Test Windows APIs separately from Ruby/OpenSSL and CEF. They need not share a certificate implementation.
5. If sign-in opens the browser, check SketchUp's own account UI after the callback. A browser success page alone is insufficient.
6. Inspect listener addresses without capturing callback query strings. Callbacks must stay on loopback; do not open public firewall ports.
7. Do not enable verbose URL, browser-cookie or packet logging during authentication. Do not use certificate-ignore flags.

## Rollback

Close SketchUp normally after saving any user model. Preserve the current state privately. Restore the pre-networking launcher from the local networking snapshot; retain the new helper and generated files as inactive evidence rather than deleting unrelated paths. The protected complete Plugin Golden backup remains available for full recovery.

A full prefix/registry restore can remove account state created after the snapshot. Use it only deliberately, with SketchUp closed, and sign in legitimately again if needed. Never copy credentials from Windows. Historical Golden tags and their complete backups are preserved. The Ruby bootstrap is an original support file, not a licensed third-party plugin; restore or quarantine only that receipt-owned file when undoing networking support.

## Primary references

- [SketchUp sign-in flow](https://help.sketchup.com/en/logging-in-sketchup)
- [SketchUp connectivity troubleshooting](https://help.sketchup.com/en/troubleshooting/problems-connecting-internet)
- [Exact Wine host-root import implementation](https://github.com/ValveSoftware/wine/blob/7f99e78815ff702ee8585a3b19ead2c59f553cdf/dlls/crypt32/unixlib.c)
- [Exact Wine root synchronization implementation](https://github.com/ValveSoftware/wine/blob/7f99e78815ff702ee8585a3b19ead2c59f553cdf/dlls/crypt32/rootstore.c)
- [Exact Wine browser argument handling](https://github.com/ValveSoftware/wine/blob/7f99e78815ff702ee8585a3b19ead2c59f553cdf/programs/winebrowser/main.c)
- [SketchUp HtmlDialog API](https://ruby.sketchup.com/UI/HtmlDialog.html)
- [SketchUp HTTP Request API](https://ruby.sketchup.com/Sketchup/Http/Request.html)

## Account and optional-service decision

The user personally completed the core sign-in. SketchUp's own account dropdown
showed the authenticated identity and Sign Out. Subsequent actual Apps and Dock
cold launches retained the connected badge, and the saved test cube reopened.
No repeat login was requested. Connect still displayed a separate unchecked
first-use agreement. Under the user's latest instruction it is USER_ACTION_DEFERRED;
it does not block core acceptance. No terms were accepted by automation, and no
remote project was created, uploaded, modified or deleted. An empty integrated
Connect project list is not proof of completed project access.

JointPushPull, FredoCorner and V-Ray retain their earlier USER_ACTION_DEFERRED
status. The compatible SketchUcation test covers its online HTML login form;
its authenticated store operations were not tested. Ruby/OpenSSL and SketchUp's
native HTTP API were tested separately. `NATIVE_PLUGIN_HTTPS=NOT_APPLICABLE` here:
no safe native third-party HTTP action was identified without entering deferred
licensing flows. This is not a claim that every extension's private network stack
works.

## Final desktop regression and cleanup

The same assistant-created cube was saved, reopened and checked for six faces and
unchanged volume. The final reopened model was unmodified before normal close.
Existing user models were not saved or overwritten. Pointer selection, native
window restore from 3072x1856 to 2300x1500 and maximize back, Apps launch, Dock
launch and Dock focus of the same PID passed. The initial window-manager restore
request left full-size normal bounds; the actual title-bar cycle from a smaller
window established the resize result.

Actual GNOME compositor recordings covered three native right-click openings,
menu first paint, a real toolbar context menu, the online plugin dialog and
focus loss/regain. The final recordings contained 97 and 31 variable-rate frames;
no black application popup/dialog was observed. Five initial dark-region detector
flags were the normal GNOME Dock before the toolbar popup, confirmed by inspecting
those frames. Detection over the application region found no large black patch.
This is bounded recorded evidence, not a constant-60-fps claim.

The cold-launch Ruby bootstrap also rejected a deliberately untrusted loopback
TLS certificate, and CEF returned HTTPS document information through an HtmlDialog
callback. Three earlier controlled HtmlDialog close cycles and the later cold-run
close passed. Temporary server listeners and diagnostic processes stopped. No
CEF debug port or test proxy was configured. The default browser, DNS/filtering,
firewall and system trust policy were unchanged. Mouse acceleration returned to
its original default, the original keyboard layout was restored, and Input Lock
reported SAFE_NORMAL with zero grabbed devices.

Each of the three test closes reached zero prefix processes. A new canonical
SketchUp launch appeared afterward with a modified model; it was left untouched.
Its live processes belong to the current canonical service, whose Restart is no.
They are not stale test processes. Unrelated Wine applications were preserved.

See [network-acceptance.json](network-acceptance.json) for the scoped gate record.
The current support change adds mandatory network/account review gates to the
[update framework](UPDATE.md); 54 automated tests passed with zero skips. This
does not validate any future SketchUp/runtime version.

## Reproduce the diagnostic checks

Keep test files and all output in a private directory. Never supply an auth URL,
account endpoint, cookie, token or password to a diagnostic probe. Compare host
and container results before changing trust. A received 3xx/4xx HTTP response
can still demonstrate successful TLS; distinguish it from full service access.

In SketchUp's Ruby Console, an ordinary synchronous request tests the initialized
OpenSSL store without replacing it:

```ruby
require 'net/http'
u = URI('https://example.com/')
h = Net::HTTP.new(u.host, u.port)
h.use_ssl = true
h.open_timeout = h.read_timeout = 8
puts h.get('/').code
```

For CEF, create a `UI::HtmlDialog`, call `set_url('https://example.com/')`, and
verify the document host/protocol with `execute_script` and an
`add_action_callback` after loading. Keep a reference to the dialog and close it
normally. Do not enable a remote debugging port. The successful local test used
a one-shot UI timer and no background Ruby thread.

Original Windows probe sources are included; no executable is distributed:

```sh
x86_64-w64-mingw32-gcc -municode tests/network-probe.c tests/network-wininet.c \
  -lwinhttp -lwininet -lws2_32 -o "$PRIVATE_TESTS/network-probe.exe"
```

Run that probe only in the exact private runtime/prefix environment after closing
SketchUp normally. The following example uses the installed launcher's environment
and runtime wrapper, with explicit `SKETCHUP_ROOT` and `PRIVATE_TESTS` environment
variables set by the operator:

```python
import os, runpy, subprocess
from pathlib import Path
root = Path(os.environ['SKETCHUP_ROOT']).resolve(strict=True)
private = Path(os.environ['PRIVATE_TESTS']).resolve(strict=True)
api = runpy.run_path(str(root / 'bin/launch-sketchup.py'))
get_processes = api['processes']
make_environment = api['environment']
assert not get_processes(root / 'compatdata'), 'Close SketchUp first'
env = os.environ.copy()
env.update(make_environment(root, private))
for key in ('WAYLAND_DISPLAY', 'WINEPREFIX', 'LD_PRELOAD', 'LD_LIBRARY_PATH',
            'SU_CEF_DBG_PORT', 'QT_SCALE_FACTOR', 'QT_SCREEN_SCALE_FACTORS'):
    env.pop(key, None)
command = [str(root / 'runtime/SteamLinuxRuntime_sniper/_v2-entry-point'),
           '--verb=run', '--', '/usr/bin/python3',
           str(root / 'bin/runtime-exec.py'), str(root),
           str(root / 'runtime/GE-Proton10-25/proton'), 'run',
           'Z:' + str(private / 'network-probe.exe'), 'https://example.com/']
subprocess.run(command, env=env, check=True, timeout=80)
```

Inspect `WINHTTP` and `WININET` success/error/status lines in the private Proton
log; the process exit code alone is not the diagnostic result. The probes disable
cookies/cache writes and automatic redirects where supported; neither bypasses
certificate validation. Compile/run requirements are optional diagnostic tooling,
not a dependency for daily launching.

For a negative TLS test, serve a disposable self-signed certificate only on
127.0.0.1, never add it to any trust store, and expect certificate-verification
failure in the host, container, Wine and Ruby. Stop the server and verify the
listener is absent. Keep its key/certificate and output private. Never substitute
an external interception service or disable verification to make the test pass.

## Subsequent Hebrew-input regression

The input repair preserved the authenticated session and secure networking. Fresh probes returned verified Ruby HTTPS results for example.com (200), SketchUp (301) and SketchUcation (200), SketchUp HTTP API 200, and an HTTPS Example Domain HtmlDialog callback. TLS verification stayed enabled and the existing host-trust bootstrap was applied. The plugin online form loaded again without submitting credentials or accepting terms. [Hebrew regression](HEBREW-INPUT.md) supplies the associated cold-launch/input evidence. Optional service outcomes above remain unchanged.

## Bundled extension version drift

The final integrity audit found Add Location 1.8.6 and AI Assistant 1.0.5 in the
current prefix, versus 1.8.2 and 1.0.3 in the protected Plugin Golden. Their change
timestamps predate the Hebrew task and fall near the beginning of this networking
session. The exact update mechanism is not established. Migrated third-party
plugin code remains unchanged. [Current plugin inventory and limits](PLUGINS.md)
record this separately from the unchanged application/runtime binary hashes.
