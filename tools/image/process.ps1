python tools/image/resize.py resource/base/image/Items resource/base/image/Items_resized --width 113 --height 113

python tools/image/crop.py resource/base/image/Items_resized resource/base/image/Items_cropped --box 16 12 82 57

python tools/image/transparency2green.py resource/base/image/Items_cropped resource/base/image/Items_processed

Remove-Item -Path "resource/base/image/Items_resized" -Recurse -Force
Remove-Item -Path "resource/base/image/Items_cropped" -Recurse -Force

Write-Host "Process Completed" -ForegroundColor Green
