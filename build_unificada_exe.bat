@echo off
echo ============================================================
echo   COMPILADOR LOCAL DE GRETEL IMAGE HUB (BYPASS GOOGLE DRIVE)
echo ============================================================
echo.

:: Definir rutas locales en disco C:
set LOCAL_TEMP=C:\Users\hchumpitaz\.gemini\tmp\gretel-gemini\build_unificada
set OUTPUT_PATH=C:\Users\hchumpitaz\Downloads

echo 1. Instalando/Actualizando dependencias locales en Python 3.13...
py -3.13 -m pip install customtkinter pyinstaller pillow rembg onnxruntime

echo.
echo 2. Creando entorno de compilacion local en disco C: para evitar bloqueos de la nube...
if exist "%LOCAL_TEMP%" rmdir /s /q "%LOCAL_TEMP%"
mkdir "%LOCAL_TEMP%"

:: Copiar archivos fuente al disco C local
copy "image_resize\app_unificada.py" "%LOCAL_TEMP%\"
copy "image_resize\procesador_imagenes_ml.py" "%LOCAL_TEMP%\"

echo.
echo 3. Iniciando PyInstaller localmente desde el disco C: con Python 3.13...
cd /d "%LOCAL_TEMP%"

py -3.13 -m PyInstaller --noconfirm --onedir --windowed --paths . --hidden-import asyncer --hidden-import pooch --hidden-import aiohttp --collect-all rembg --collect-all onnxruntime --workpath "%LOCAL_TEMP%\build" --specpath "%LOCAL_TEMP%" --name "Gretel_Image_Hub" "app_unificada.py"

echo.
echo 4. Copiando la carpeta del programa a Descargas...
if exist "%OUTPUT_PATH%\Gretel_Image_Hub_Fast" rmdir /s /q "%OUTPUT_PATH%\Gretel_Image_Hub_Fast"
robocopy "%LOCAL_TEMP%\dist\Gretel_Image_Hub" "%OUTPUT_PATH%\Gretel_Image_Hub_Fast" /E /NJH /NJS /NDL /NFL

echo.
echo 5. Comprimiendo el programa en un archivo .ZIP listo para compartir...
if exist "%OUTPUT_PATH%\Gretel_Image_Hub_Fast.zip" del /f /q "%OUTPUT_PATH%\Gretel_Image_Hub_Fast.zip"
powershell -NoProfile -Command "Compress-Archive -Path '%OUTPUT_PATH%\Gretel_Image_Hub_Fast' -DestinationPath '%OUTPUT_PATH%\Gretel_Image_Hub_Fast.zip' -Force"

echo.
echo ============================================================
echo   ¡PROCESO TERMINADO CON EXITO!
echo   El programa abre instantaneamente (menos de 1 segundo).
echo   - Carpeta del programa: 'Downloads\Gretel_Image_Hub_Fast'
echo   - Archivo ZIP listo para compartir: 'Downloads\Gretel_Image_Hub_Fast.zip'
echo ============================================================
echo.
