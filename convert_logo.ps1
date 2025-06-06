$imagePath = "attached_assets\image_1745331312173.png"
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($imagePath))
Write-Output $base64 