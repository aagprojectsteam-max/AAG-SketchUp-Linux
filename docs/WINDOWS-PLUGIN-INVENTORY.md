# Windows extension inventory

Audit date: 2026-09-28. The Windows installation was used only as a source. No
Windows application, installer, registry hive, licensing service, or extension
was executed. The audit reads files without loading Ruby or native modules.
Raw inventories remain private because they contain source paths and filenames.

## Locations and duplicates

| Location | Finding |
|---|---|
| Windows user SketchUp 2026 `Plugins` | 12 loader scripts; 1,944 files, 39,628,538 bytes |
| Windows ProgramData SketchUp 2026 `Plugins` | V-Ray loader and companion directory; 2 files |
| Application `ShippedExtensions` | Six bundled extensions; duplicates of user-installed bundled extensions |
| Application `plugins` | Qt framework plugins, not SketchUp Ruby extensions |
| Older local SketchUp 2023–2025 folders | Application history/cache; no additional Ruby extension payload found |
| Windows Downloads | SketchUcationTools RBZ; 143 archive members; loader matches installed 5.0.6 |
| Chaos Program Files | Cosmos, UnifiedLogin, V-Ray; 1,270 files, 2,370,619,880 bytes |
| Vendor user data | Fredo defaults/vaults and Chaos cloud/settings directories; inventoried separately and not copied |

Windows extension preferences mark the present extensions enabled. Historical
preferences also mention CenterPointAll and older bundled versions. A settings
entry alone does not establish an installed extension: no CenterPointAll loader
was found in the inspected extension roots.

## Versions and compatibility classes

A: Ruby/assets. B: native module. C: external service. D: renderer/GPU.
E: licensing. F: unknown implementation. Flags describe dependencies rather than
claiming that an extension was tested successfully.

| Extension | Windows version | Primary class / flags | Risk | Required dependencies |
|---|---|---|---|---|
| Pipe Along Path | 2.2, 2014-11-12 | A | Low | SketchUp Ruby geometry API |
| KBS Face Tool | 1.0.0 | A; encrypted Ruby | Low | SketchUp Ruby API; internal behavior inspected through tests |
| SketchUcation | 5.0.6 | B / C, E | Medium | Ruby 3.2 native licensing library; HTML dialogs; online store |
| LibFredo6 | 15.8e, 2026-02-15 | B | Medium | Ruby 3.2 native library; HTML dialogs |
| JointPushPull | 4.9a, 2024-04-02 | A / B, E | Medium | LibFredo6 >= 15.3; SketchUcation licensing |
| FredoCorner | 2.7a, 2024-03-31 | A / B, E | Medium | LibFredo6 >= 14.3; SketchUcation licensing |
| V-Ray for SketchUp | 7.30.00, 2026-04-06 | D / B, C, E | High | Matching SketchUp integration, VC runtime, Ruby 3.2, Chaos agreement/license; optional Cosmos/login helpers |
| Add Location | 1.8.2 | C / E | Medium | Trimble online services and entitlement |
| AI Assistant | 1.0.3 | C / E | Medium | Trimble online services and entitlement |
| AI Render | 1.2026.02.26 | D / B, C, E | High | Ruby 3.2, matching Qt 6.9 native bridge, online entitlement |
| Dynamic Components | 1.8.3 | A | Low | Ruby API; Linux Golden already contains newer 1.8.5 |
| Migrate Extensions | 1.0.1 | A | Medium | Filesystem access; do not use it to bulk-import Windows state |
| Sandbox Tools | 2.3.5 | A | Low | Ruby geometry API |

## Native modules

The user plugin tree contains 15 x86-64 and two historical x86 PE files. The
shipped extension tree contains three x86-64 PE files. The complete Chaos payload
contains 299 x86-64 and 150 x86 PE files, including helper/runtime components.
These counts include inactive version-specific payloads, not just loaded DLLs.

LibFredo6 `Win64_32` and SketchUcation `Win64_32` import
`x64-ucrt-ruby320.dll`; the candidate reports Ruby 3.2.2. Historical Win32 and
Ruby 1.8–3.1 modules must not be selected by SketchUp 2026. The matching native
libraries are extracted by their vendors into the candidate's own Windows
AppData Temp directory. That is a regenerable vendor cache, not a dependency on
an external Linux temporary installation.

The bundle also contains macOS native libraries, including universal x86-64 /
ARM64 libraries. They are inactive platform payloads. Their presence is distinct
from the original defective ARM64 Windows MSVCP140.dll. The audit identifies
Mach-O headers as well as PE headers, imports, hashes and fixed file versions.

V-Ray contains separate SketchUp 2021–2026 and Ruby 2.7/3.2 integrations. A
successful loader or toolbar is insufficient: a supported local render, output,
cancellation, shutdown and licensing workflow must pass before promotion.

## Private state

No Windows license files, cookies, cloud tokens, browser profiles, whole AppData
folders, registry hives or account directories are migration inputs. Existing
Fredo parameter/vault files are recorded separately. Opaque settings require
individual review and remain untouched. An unclassified PDF inside the
LibFredo6 source folder is not needed for extension execution and is excluded
from production migration.
