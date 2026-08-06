@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_5
echo Source: rem=973772056108597139664192806
echo Center d=950217236152435230647280238804780114408918340747
echo m partner=121858544374731443100730035156
echo Range a67136eae0bd410e5ceff2b34e52c2fbbde8c48b:a67136eae0bd410e5ceff2b34e52c4cd6732e48b  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a67136eae0bd410e5ceff2b34e52c2fbbde8c48b:a67136eae0bd410e5ceff2b34e52c4cd6732e48b -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
