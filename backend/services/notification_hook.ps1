# PowerShell script to hook into Windows notifications in real-time
# This script runs as a background service to capture notifications

# Register for notification events
$action = {
    param($event)
    $xml = $event.ToXml()
    $message = $event.Message
    
    # Extract notification data
    $appId = "Unknown"
    $title = "Notification"
    $body = ""
    
    # Try to extract from XML
    if ($xml -match '<Data Name="ApplicationId">([^<]+)</Data>') {
        $appId = $matches[1]
    }
    
    # Try to extract Toast XML
    if ($xml -match '<Data Name="ToastXml">(.+?)</Data>') {
        $toastXml = $matches[1]
        try {
            # Decode HTML entities
            $toastXmlDecoded = $toastXml -replace '&lt;', '<' -replace '&gt;', '>' -replace '&amp;', '&' -replace '&quot;', '"'
            
            # Parse XML
            $toastDoc = New-Object System.Xml.XmlDocument
            $toastDoc.LoadXml($toastXmlDecoded)
            
            # Extract text elements
            $textNodes = $toastDoc.SelectNodes("//text")
            if ($textNodes.Count -gt 0) {
                $title = $textNodes[0].InnerText
            }
            if ($textNodes.Count -gt 1) {
                $body = ($textNodes | Select-Object -Skip 1 | ForEach-Object { $_.InnerText }) -join " "
            }
        } catch {
            # If parsing fails, try regex
            if ($toastXml -match '<text[^>]*>([^<]+)</text>') {
                $allMatches = [regex]::Matches($toastXml, '<text[^>]*>([^<]+)</text>')
                if ($allMatches.Count -gt 0) {
                    $title = $allMatches[0].Groups[1].Value
                }
                if ($allMatches.Count -gt 1) {
                    $body = ($allMatches | Select-Object -Skip 1 | ForEach-Object { $_.Groups[1].Value }) -join " "
                }
            }
        }
    }
    
    # Output notification data as JSON
    $notification = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        AppName = $appId
        Title = $title
        Body = $body
    } | ConvertTo-Json -Compress
    
    # Write to output file for Python to read
    $outputFile = Join-Path $PSScriptRoot "notification_capture.json"
    $notification | Out-File -FilePath $outputFile -Encoding UTF8 -Append
}

# Register event subscription
Register-WmiEvent -Query "SELECT * FROM Win32_NTLogEvent WHERE LogFile='Microsoft-Windows-UserNotificationsPlatform/Operational' AND EventCode=1001" -Action $action

# Keep script running
while ($true) {
    Start-Sleep -Seconds 1
}

