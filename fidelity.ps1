[CmdletBinding()]
Param(
    $Year = (Get-Date -Format "yyyy") - 1,
    $DataFile = "./data/$($Year).TransactionHistory.csv"
)

Begin {

    $ConversionRates = (Invoke-WebRequest -Uri "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/vybrane.txt?od=1.1.$Year&do=31.12.$($Year+1)&mena=USD").Content -Split "`n"
        | Select-Object -Skip 1
        | ConvertFrom-Csv -Delimiter "|"
        | ForEach-Object {
            [PSCustomObject]@{"date" = [datetime]::parseexact($_.Datum, "dd.MM.yyyy", $null); "rate" = [double]::Parse($_.kurz) }
        }


    filter Get-ConversionRate {
        Param(
            $Date = (Get-Date)
        )

        $result = ($ConversionRates | Where-Object { $_.date -le $Date } | Select-Object -Last 1).rate

        $ConversionRates | ForEach-Object {
            Write-Host "$($_.date) -le $Date =>" $((Get-Date $_.date) -le (Get-Date $Date))
        }

        $result
    }

    filter ConvertFrom-Usd {
        Param(
            $Date = (Get-Date)
        )

        $_ * (Get-ConversionRate -Date $Date)
    }

    filter ParseFloat {
        [double]::Parse(($_ -replace "(-?)\D+([\d.]+)",'$1$2' -replace "\.",","))
    }
}

Process {
    $data = Get-Content $DataFile | ConvertFrom-Csv -Delimiter ','
    $ESPP = $data | Where-Object { $_."Transaction type" -match 'YOU BOUGHT ESPP###' }

    $ESPP | ForEach-Object {
        $transactionDate = [datetime]::parseexact(($_."Transaction date"), "MMM-dd-yyyy", [cultureinfo]::CreateSpecificCulture('en-US'))
        [PSCustomObject]@{
            AmountCZK = $_.Amount | ParseFloat | ConvertFrom-Usd -Date $transactionDate
            AmountUSD = $_.Amount | ParseFloat
            Date = $transactionDate
        }   
    }
}

End {
}
