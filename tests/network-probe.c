/* SPDX-License-Identifier: MIT
 * Original HTTPS diagnostic. Inspect success/error/status fields, not exit code.
 * Use only non-secret test URLs; no auth callbacks or account endpoints.
 */
#define _UNICODE
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <winhttp.h>
#include <stdio.h>

void wininet_test(const wchar_t*,const wchar_t*);
int wmain(int argc,wchar_t **argv) {
 if(argc!=2)return 2;
 URL_COMPONENTS u={0}; wchar_t host[512],path[2048];u.dwStructSize=sizeof(u);u.lpszHostName=host;u.dwHostNameLength=512;u.lpszUrlPath=path;u.dwUrlPathLength=2048;
 if(!WinHttpCrackUrl(argv[1],0,0,&u)||u.nScheme!=INTERNET_SCHEME_HTTPS)return 3;
 WSADATA ws;WSAStartup(MAKEWORD(2,2),&ws);ADDRINFOW *ai=NULL;int dns=GetAddrInfoW(host,L"443",NULL,&ai);wprintf(L"DNS host=%ls result=%d\n",host,dns);if(ai)FreeAddrInfoW(ai);WSACleanup();
 HINTERNET s=WinHttpOpen(L"AAG-SketchUp-Network-Diagnostic/1.0",WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,WINHTTP_NO_PROXY_NAME,WINHTTP_NO_PROXY_BYPASS,0);
 WinHttpSetTimeouts(s,8000,8000,8000,8000);HINTERNET c=WinHttpConnect(s,host,u.nPort,0),r=WinHttpOpenRequest(c,L"HEAD",path,NULL,WINHTTP_NO_REFERER,WINHTTP_DEFAULT_ACCEPT_TYPES,WINHTTP_FLAG_SECURE);
 DWORD disable=WINHTTP_DISABLE_COOKIES,redirect=WINHTTP_OPTION_REDIRECT_POLICY_NEVER;
 WinHttpSetOption(r,WINHTTP_OPTION_DISABLE_FEATURE,&disable,sizeof(disable));WinHttpSetOption(r,WINHTTP_OPTION_REDIRECT_POLICY,&redirect,sizeof(redirect));
 BOOL ok=WinHttpSendRequest(r,WINHTTP_NO_ADDITIONAL_HEADERS,0,WINHTTP_NO_REQUEST_DATA,0,0,0)&&WinHttpReceiveResponse(r,NULL);DWORD error=ok?0:GetLastError(),status=0,n=sizeof(status);if(ok)WinHttpQueryHeaders(r,WINHTTP_QUERY_STATUS_CODE|WINHTTP_QUERY_FLAG_NUMBER,NULL,&status,&n,NULL);
 wprintf(L"WINHTTP host=%ls success=%d error=%lu status=%lu tls_validation=ENFORCED\n",host,ok,error,status);if(r)WinHttpCloseHandle(r);if(c)WinHttpCloseHandle(c);if(s)WinHttpCloseHandle(s);
 wininet_test(argv[1],host);return 0;
}
