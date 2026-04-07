$root = "dc=t,dc=goauthentik,dc=io"
$domain = "t.goauthentik.io"

$rootOU = New-ADOrganizationalUnit `
    -Name "ak-test" `
    -Path $root `
    -PassThru

$userErinH = New-ADUser `
    -GivenName "Erin M." `
    -Surname "Hagens" `
    -Name "Erin M. Hagens" `
    -UserPrincipalName "erin.h@$domain" `
    -SamAccountName "erin.h" `
    -PasswordNotRequired $true `
    -Path $rootOU.DistinguishedName `
    -Enabled $true `
    -PassThru

New-ADUser `
    -GivenName "Deactivated" `
    -Surname "Account" `
    -Name "Deactivated Account" `
    -UserPrincipalName "deactivated.a@$domain" `
    -SamAccountName "deactivated.a" `
    -Enabled $false `
    -Path $rootOU.DistinguishedName

$groupTest = New-ADGroup `
    -Name "Test Group" `
    -Path $rootOU.DistinguishedName `
    -GroupCategory Security `
    -GroupScope Global `
    -PassThru

Add-ADGroupMember `
    -Identity $groupTest `
    -Members $userErinH
