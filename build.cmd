chcp 65001

set SOURCE_DIR="node_modules/@mdi/font/"
set TARGET_DIR="custom_components/panel_iframe/www/mdi/"

echo SOURCE_DIR
echo TARGET_DIR

xcopy %SOURCE_DIR%preview.html %TARGET_DIR% /F /Y

xcopy %SOURCE_DIR%css %TARGET_DIR%css /F /Y

xcopy %SOURCE_DIR%fonts %TARGET_DIR%fonts /F /Y

del package-lock.json