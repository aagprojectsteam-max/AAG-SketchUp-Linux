/* Original test control. Reports only its own four EDIT fields.
 * Output contains test input: keep it private and use a new test path. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <stdio.h>
#include <stdint.h>
static HWND top, fields[4];static wchar_t output[2048];
static void report(void){FILE *f=_wfopen(output,L"w");if(!f)return;HKL list[32];int n=GetKeyboardLayoutList(32,list);HWND focus=GetFocus();int idx=-1;for(int i=0;i<4;i++)if(focus==fields[i])idx=i;
fprintf(f,"{\"pid\":%lu,\"active\":%s,\"focused_row\":%d,\"hkl\":\"%llx\",\"layouts\":[",GetCurrentProcessId(),GetForegroundWindow()==top?"true":"false",idx,(unsigned long long)(uintptr_t)GetKeyboardLayout(0));for(int i=0;i<n&&i<32;i++)fprintf(f,"%s\"%llx\"",i?",":"",(unsigned long long)(uintptr_t)list[i]);fprintf(f,"],\"values_codepoints\":[");for(int i=0;i<4;i++){wchar_t b[1024];int len=GetWindowTextW(fields[i],b,1024);fprintf(f,"%s[",i?",":"");for(int k=0;k<len;k++)fprintf(f,"%s%u",k?",":"",(unsigned)b[k]);fprintf(f,"]");}fprintf(f,"]}\n");fclose(f);}
static LRESULT CALLBACK proc(HWND h,UINT m,WPARAM w,LPARAM l){switch(m){case WM_CREATE:for(int i=0;i<4;i++){const wchar_t *labels[]={L"English 1",L"Hebrew 1",L"English 2",L"Hebrew 2"};CreateWindowW(L"STATIC",labels[i],WS_CHILD|WS_VISIBLE,20,25+i*70,130,35,h,0,0,0);fields[i]=CreateWindowExW(WS_EX_CLIENTEDGE,L"EDIT",L"",WS_CHILD|WS_VISIBLE|WS_TABSTOP|ES_AUTOHSCROLL,155,20+i*70,590,45,h,(HMENU)(INT_PTR)(100+i),0,0);}SetTimer(h,1,100,0);break;case WM_TIMER:report();break;case WM_INPUTLANGCHANGE:report();break;case WM_DESTROY:report();PostQuitMessage(0);return 0;}return DefWindowProcW(h,m,w,l);}
int wmain(int argc,wchar_t **argv){if(argc!=2)return 2;wcsncpy(output,argv[1],2047);SetProcessDPIAware();HINSTANCE inst=GetModuleHandleW(NULL);WNDCLASSW cls={0};cls.lpfnWndProc=proc;cls.hInstance=inst;cls.lpszClassName=L"AAGInputProbe";cls.hbrBackground=(HBRUSH)(COLOR_WINDOW+1);cls.hCursor=LoadCursor(NULL,IDC_ARROW);RegisterClassW(&cls);top=CreateWindowW(cls.lpszClassName,L"AAG Plain Wine Input Test",WS_OVERLAPPEDWINDOW|WS_VISIBLE,300,230,800,390,NULL,NULL,inst,NULL);ShowWindow(top,SW_SHOW);SetForegroundWindow(top);SetFocus(fields[0]);MSG msg;while(GetMessageW(&msg,NULL,0,0)>0){if(!IsDialogMessageW(top,&msg)){TranslateMessage(&msg);DispatchMessageW(&msg);}}return 0;}
