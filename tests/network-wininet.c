/* SPDX-License-Identifier: MIT
 * Original HTTPS diagnostic. Inspect success/error/status fields, not exit code.
 * Use only non-secret test URLs; no auth callbacks or account endpoints.
 */
#define _UNICODE
#include <windows.h>
#include <wininet.h>
#include <stdio.h>
void wininet_test(const wchar_t *url,const wchar_t *host) {
 HINTERNET s=InternetOpenW(L"AAG-SketchUp-Network-Diagnostic/1.0",INTERNET_OPEN_TYPE_PRECONFIG,NULL,NULL,0);DWORD timeout=8000;InternetSetOptionW(s,INTERNET_OPTION_CONNECT_TIMEOUT,&timeout,sizeof(timeout));InternetSetOptionW(s,INTERNET_OPTION_RECEIVE_TIMEOUT,&timeout,sizeof(timeout));
 HINTERNET r=InternetOpenUrlW(s,url,NULL,0,INTERNET_FLAG_SECURE|INTERNET_FLAG_NO_COOKIES|INTERNET_FLAG_NO_CACHE_WRITE|INTERNET_FLAG_NO_AUTO_REDIRECT,0);DWORD error=r?0:GetLastError();DWORD status=0,n=sizeof(status);if(r)HttpQueryInfoW(r,HTTP_QUERY_STATUS_CODE|HTTP_QUERY_FLAG_NUMBER,&status,&n,NULL);
 wprintf(L"WININET host=%ls success=%d error=%lu status=%lu tls_validation=ENFORCED\n",host,r!=NULL,error,status);if(r)InternetCloseHandle(r);if(s)InternetCloseHandle(s);}
