# Export the polished deck PPTX to PDF via PowerPoint COM (one-off helper).
param(
    [string]$Pptx = "docs\HireFit_Ranker_Redrob_POLISHED.pptx",
    [string]$Pdf  = "docs\HireFit_Ranker_Redrob_POLISHED.pdf"
)
$pptxPath = (Resolve-Path $Pptx).Path
$pdfPath  = Join-Path (Get-Location) $Pdf
$pp = New-Object -ComObject PowerPoint.Application
try {
    $pres = $pp.Presentations.Open($pptxPath, $true, $false, $false)  # readonly, no window
    $pres.SaveAs($pdfPath, 32)  # 32 = ppSaveAsPDF
    $pres.Close()
    Write-Output "exported $pdfPath"
} finally {
    $pp.Quit()
}
