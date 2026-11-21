"""
Centralizes predefined responses intended for integration testing, especially when used with the `server` fixture.
For standard tests, responses should be encapsulated within the test itself. This module should be referenced
primarily when updating the responses for the integration test client, ensuring a consistent test environment.

Key Benefits:
    - Central repository of standardized test responses.
    - Promotes consistent and maintainable testing practices.

Usage:
    1. Import the required response constant from this module:
       from tests.fixtures.responses import SECTORS

    2. Incorporate the imported response in your test logic:
       def test_client_get_sectors_status(server):
           server.add(responses.POST, "https://example.com/api/areas", body=SECTORS, status=200)
           # Continue with the test...
"""

LOGIN = """
    {
        "SessionId": "00000000-0000-0000-0000-000000000000",
        "Username": "test",
        "Domain": "domain",
        "Language": "en",
        "IsActivated": true,
        "ShowTimeZoneControls": true,
        "TimeZone": "(UTC+01:00) Amsterdam, Berlino, Berna, Roma, Stoccolma, Vienna",
        "ShowChronothermostat": false,
        "ShowThumbnails": false,
        "ShowExtinguish": false,
        "IsConnected": true,
        "IsLoggedIn": false,
        "IsLoginInProgress": false,
        "CanElevate": true,
        "Panel": {
            "Description": "T-800 1.0.1",
            "LastConnection": "01/01/1984 13:27:28",
            "LastDisconnection": "01/10/1984 13:27:18",
            "Major": 1,
            "Minor": 0,
            "SourceIP": "10.0.0.1",
            "ConnectionType": "EthernetWiFi",
            "DeviceClass": 92,
            "Revision": 1,
            "Build": 1,
            "Brand": 0,
            "Language": 0,
            "Areas": 4,
            "SectorsPerArea": 4,
            "TotalSectors": 16,
            "Inputs": 24,
            "Outputs": 24,
            "Operators": 64,
            "SectorsInUse": [
                true,
                true,
                true,
                true,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false,
                false
            ],
            "Model": "T-800",
            "LoginWithoutUserID": true,
            "AdditionalInfoSupported": 1,
            "IsFirePanel": false
        },
        "AccountId": 100,
        "ManagedAccounts": [
            {
                "Id": 1,
                "FullUsername": "domain\\\\test"
            }
        ],
        "IsManaged": false,
        "Message": "",
        "DVRPort": "",
        "ExtendedAreaInfoOnStatusPage": true,
        "DefaultPage": "Status",
        "NotificationTitle": "",
        "NotificationText": "",
        "NotificationDontShowAgain": true,
        "Redirect": false,
        "IsElevation": false,
        "InstallerForceSupervision": true,
        "PrivacyLink": "/PrivacyAndTerms/v1/Informativa_privacy_econnect_2020_09.pdf",
        "TermsLink": "/PrivacyAndTerms/v1/CONTRATTO_UTILIZZATORE_FINALE_2020_02_07.pdf"
    }"""

UPDATES = """
    {
        "ConnectionStatus": false,
        "CanElevate": false,
        "LoggedIn": false,
        "LoginInProgress": false,
        "Areas": true,
        "Events": false,
        "Inputs": true,
        "Outputs": false,
        "Anomalies": false,
        "ReadStringsInProgress": false,
        "ReadStringPercentage": 0,
        "Strings": 0,
        "ManagedAccounts": false,
        "Temperature": false,
        "StatusAdv": false,
        "Images": false,
        "AdditionalInfoSupported": true,
        "HasChanges": true
    }
"""

SYNC_LOGIN = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""

SYNC_LOGOUT = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""

SYNC_SEND_COMMAND = """[
    {
        "Poller": {"Poller": 1, "Panel": 1},
        "CommandId": 5,
        "Successful": true
    }
]"""

STRINGS = """[
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 0,
        "Description": "S1 Living Room",
        "Created": "/Date(1546004120767+0100)/",
        "Version": "AAAAAAAAgPc="
    },
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 1,
        "Description": "S2 Bedroom",
        "Created": "/Date(1546004120770+0100)/",
        "Version": "AAAAAAAAgPg="
    },
    {
        "AccountId": 1,
        "Class": 9,
        "Index": 2,
        "Description": "S3 Outdoor",
        "Created": "/Date(1546004147490+0100)/",
        "Version": "AAAAAAAAgRs="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 0,
        "Description": "Entryway Sensor",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 1,
        "Description": "Outdoor Sensor 1",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 10,
        "Index": 2,
        "Description": "Outdoor Sensor 2",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 3,
        "Class": 10,
        "Index": 3,
        "Description": "Outdoor Sensor 3",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 0,
        "Description": "Output 1",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 1,
        "Description": "Output 2",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 1,
        "Class": 12,
        "Index": 2,
        "Description": "Output 3",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    },
    {
        "AccountId": 3,
        "Class": 12,
        "Index": 3,
        "Description": "Output 4",
        "Created": "/Date(1546004147493+0100)/",
        "Version": "AAAAAAAAgRw="
    }
]"""

AREAS = """[
   {
       "Active": true,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 1,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": true,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 2,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "ActivePartial": false,
       "Max": false,
       "Activable": false,
       "ActivablePartial": false,
       "InUse": true,
       "Id": 3,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "ActivePartial": false,
       "Max": false,
       "Activable": true,
       "ActivablePartial": false,
       "InUse": false,
       "Id": 4,
       "Index": 3,
       "Element": 5,
       "CommandId": 0,
       "InProgress": false
   }
]"""

INPUTS = """[
   {
       "Alarm": true,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": true,
       "IsVideo": false,
       "Id": 1,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": true,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": true,
       "IsVideo": false,
       "Id": 2,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": false,
       "MemoryAlarm": false,
       "Excluded": true,
       "InUse": true,
       "IsVideo": false,
       "Id": 3,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Alarm": false,
       "MemoryAlarm": false,
       "Excluded": false,
       "InUse": false,
       "IsVideo": false,
       "Id": 42,
       "Index": 3,
       "Element": 4,
       "CommandId": 0,
       "InProgress": false
   }
]"""

OUTPUTS = """[
   {
       "Active": true,
       "InUse": true,
       "DoNotRequireAuthentication": true,
       "ControlDeniedToUsers": false,
       "Id": 400258,
       "Index": 0,
       "Element": 1,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "InUse": true,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": false,
       "Id": 400259,
       "Index": 1,
       "Element": 2,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "InUse": true,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": true,
       "Id": 400260,
       "Index": 2,
       "Element": 3,
       "CommandId": 0,
       "InProgress": false
   },
   {
       "Active": false,
       "InUse": false,
       "DoNotRequireAuthentication": false,
       "ControlDeniedToUsers": false,
       "Id": 400261,
       "Index": 3,
       "Element": 4,
       "CommandId": 0,
       "InProgress": false
   }
]"""

STATUS_PAGE = """
<script type="text/javascript">
    var sessionTimeout = 1200000;
    var apiURL = 'https://connect.elmospa.com/api/';
    var sessionId = 'f8h23b4e-7a9f-4d3f-9b08-2769263ee33c';

    var canElevate = '1';
    var connectionStatus = '1';
    var loggedIn = '0';
    var loggedInProgress = '0';
    var isUserIdRequired = 'False' == "True";
    var isFirePanel = 'False' == "True";
    var lastStatusAdvId = '0';

    var readStringsInProgress = 0;
    var strings = 1;
    var sendCommandCntrl = null;
    var managedAccountIds = [];
    var wantToChangeNameOrCode = 0;
    var wantToActivateSysBlock = false;

            var loginUrl = '/nwd_si?webview=1';


    var successHeader = 'Successo';
    var errorHeader = 'Errore';
    var connectLabelString = 'Connessa';
    var disconnectLabelString = 'Non connessa';
    var readStringMsg = 'Lettura dati centrale completata con successo.';
    var panelLoginButtonString = 'Accedi';
    var panelExitButtonString = 'Esci';
    var panelLoadingButtonString = 'In corso';
    var panelBusyButtonString = 'In Uso';
    var capsLockMsg = 'Caps lock abilitato.';
    var okButtonText = 'Ok';
    var cancelButtonText = 'Annulla';

    var offset = 200;
    var duration = 500;
    var isSaveThermostatSettings = false;
    var tAll = 0;
    var tProgram = false;

    var logoInterval = "";
    var i = 0;

    var panelStatus;

    var isQhuboUser = 'False' == "True";

    //Tables common responsive breakpoints
    var breakpoints = [
        { name: 'brkXXL', width: 1800 },
        { name: 'brkXL', width: 1700 },
        { name: 'brkLG', width: 1400 },
        { name: 'brkMD', width: 1100 },
        { name: 'brkSM', width: 992 },
        { name: 'brkXS', width: 550 },
        { name: 'brkXXS', width: 480 }
    ]

    $(document).ready(function () {
        window.addEventListener("beforeunload", () => {

        });

        $('input[type=checkbox], input[type=radio]').customRadioCheck();
        initializeControls();
        $('.scroll-to-top').hide();

        $(window).scroll(function () {
            if ($(this).scrollTop() > offset)
                $('.scroll-to-top').fadeIn(duration);
            else
                $('.scroll-to-top').fadeOut(duration);
        });

        $('.scroll-to-top').click(function (event) {
            event.preventDefault();
            $('html, body').animate({ scrollTop: 0 }, duration);
            return false;
        });

        $('.paneldetailarrow').click(function () {
            if (!$('.paneldetailarrow i').hasClass('down')) {
                $('.paneldetailarrow i').addClass('down');
                $('#mainPanelDetail').slideDown(500);
            } else {
                $('.paneldetailarrow i').removeClass('down');
                $('#mainPanelDetail').slideUp(500);
            }
        });

        if (isQhuboUser) {
            $('.qhubo-area.area-disarmed, a.status-idle[data-elementclass=9]').hover(
                function () {
                    $(this).children('i').removeClass('icoN-login-unlock').addClass('icoN-login-lock');
                }, function () {
                    $(this).children('i').removeClass('icoN-login-lock').addClass('icoN-login-unlock');
                }
            );

            $('.qhubo-area.area-armed, a.status-armed[data-elementclass=9]').hover(
                function () {
                    $(this).children('i').removeClass('icoN-login-lock').addClass('icoN-login-unlock');
                }, function () {
                    $(this).children('i').removeClass('icoN-login-unlock').addClass('icoN-login-lock');
                }
            );
        }

        var backURL = $(this).attr("href");
        if (backURL != undefined) {
            backURL = backURL.replace('/undefined', '');
            history.pushState({}, $(this).attr("title"), backURL);

            $("a").each(function () {
                $(this).attr('href', backURL);
            });
        }

        setTimeout(function () {
            $("#ErrorMsgBox input, #ErrorMsgBox .close").hide();
            showErrorMsg("", "Errore", "Sessione scaduta. Verrai reindirizzato alla pagina di accesso a breve.");

            setTimeout(function () {
                window.location.href = loginUrl;
            }, 3000);
        }, sessionTimeout);
    });

    $('.paneldetailarrow').click(function () {
        var isOpen = getCookie("pnlClosed");
        if (isOpen == "1")
            setCookie("pnlClosed", "0");
        else if (isOpen == "0")
            setCookie("pnlClosed", "1");
        else {
            if ($("#mainPanelDetail").is(":visible"))
                setCookie("pnlClosed", "1");
            else
                setCookie("pnlClosed", "0");
        }
    });

    $(window).resize(function () {
        initializeControls();
        roundTables();
    });

    function showLoading() {
        $('.loader').show();
    }

    function hideLoading() {
        $('.loader').hide();
    }

    function initializeControls() {
        if ($(window).width() < 979) {
            $('#infobox').insertAfter('#main_content #divDashArea');

            $('#infobox .col-4').unbind('click').click(function (e) {
                if ($(e.target).hasClass('h2infobox')) {
                    if (!$(this).children('.content').hasClass('opened'))
                        $(this).children('.content').addClass('opened').slideDown();
                    else
                        $(this).children('.content').removeClass('opened').slideUp();
                }
            });

            $('.infobox .col-4 .divInfobox').eq(0).next('.content').addClass('opened').show();
            $('.infobox .col-4 .divInfobox').unbind('click').click(function (e) {
                if ($(e.target).attr('id') != 'configureBtn') {
                    if ($('#configureBtn').hasClass('close'))
                        $('#configureBtn').trigger('click');

                    if (!$(this).next('.content').hasClass('opened')) {
                        $('.graph-container').css('min-height', 'auto')

                        $(this).next('.content').addClass('opened').slideDown(function () {
                            $('.graph-container').css('min-height', '400px');
                        });
                    } else {
                        $('.graph-container').css('min-height', 'auto');
                        $(this).next('.content').removeClass('opened').slideUp();
                    }

                    if ($('.infobox .col-4 .divInfobox').index(this) == 3)
                        $(window).resize();
                }
            });
        } else {
            $('#infobox .col-4 .content').removeAttr('style');
            $('.infobox .col-4 .divInfobox').removeAttr('style');
            $('#infobox').insertAfter('#main_content .dashboard-body');
            $('#infobox .col-4').unbind('click');
            $('.infobox .col-4 .divInfobox').next('.content').removeAttr('style')
        }

        if ($(window).width() < 768) {
            if (isQhuboUser) {
                $(".main-logo").attr('src', "Content/themes/theme-22/Images/footer-logo.png");
                $('.logged-panel').show();
            }

            if (!$('#main_content #divPanelDetail').length) {
                $('#divPanelDetail').appendTo('#main_content');
                $('.paneldetailarrow i').addClass('down');
            }

            if (!$('#sidebar #divLanguageOptions').length) {
                $('#divLanguageOptions').insertBefore($('#sidebar #divPanelSiteInfo').parent());
                $('#divLanguageAlign').removeClass('align-right');
            }

            $('h6').hide();
            $('#user_menu').show();
            $('#lnkLogo').prependTo('#divLogoMobile');

            setTimeout(function () {
                $('#divLanguageOptions').removeClass('visible-desktop');
            }, 300);

            if (getCookie("pnlClosed") == "1") {
                $("#mainPanelDetail").hide();
                $('.paneldetailarrow i').removeClass('down');
            } else if (getCookie("pnlClosed") == "0") {
                $("#mainPanelDetail").show();
                $('.paneldetailarrow i').addClass('down');
            } else {
                setTimeout(function () {
                    if ($('.paneldetailarrow i').hasClass('down')) {
                        $('.paneldetailarrow').click();
                        setCookie("pnlClosed", "1");
                    }
                }, 2000);
            }

            clearInterval(logoInterval);
            logoInterval = 0;

            if (!isQhuboUser)
                logoInterval = setInterval(changeHeader, 5000);
        } else if ((mobileDevices.test(navigator.userAgent) || isIOS13Devices) &&
            $(window).width() > 768 && $(window).height() < 420) {
            if (!$('.paneldetailarrow i').hasClass('down')) {
                $('.paneldetailarrow').click();
            }

            clearInterval(logoInterval);
            logoInterval = 0;
            $(".main-logo").show();
            $(".main-logo").removeClass("animate__fadeInDown");
            $(".main-logo").removeClass("animate__fadeOut");
            $(".logged-panel").hide();
            $('h6').show();
            $('#user_menu').hide();
            $('#lnkLogo').appendTo('#divLogo');

            if (isQhuboUser)
                $(".main-logo").attr('src', "Images/dashboard-logo.png");

            if (!$('.sidebar--scroll #divPanelDetail').length)
                $('#divPanelDetail').appendTo('.sidebar--scroll');

            if (!$('#main_content #divLanguageOptions').length) {
                $('#divLanguageOptions').prependTo('#main_content');
                $('#divLanguageAlign').addClass('align-right');
            }
        } else {
            clearInterval(logoInterval);
            logoInterval = 0;
            $(".main-logo").show();
            $(".main-logo").removeClass("animate__fadeInDown");
            $(".main-logo").removeClass("animate__fadeOut");
            $(".logged-panel").hide();
            $('h6').show();
            $('#user_menu').hide();
            $('#lnkLogo').appendTo('#divLogo');

            if (isQhuboUser)
                $(".main-logo").attr('src', "Images/dashboard-logo.png");

            if (!$('#sidebar #divPanelDetail').length) {
                $('#divPanelDetail').appendTo('.sidebar--scroll');
                $('#mainPanelDetail').show();
            }

            if (!$('#main_content #divLanguageOptions').length) {
                $('#divLanguageOptions').prependTo('#main_content');
                $('#divLanguageAlign').addClass('align-right');
            }
        }
    }

    function roundTables() {
        $('table.dataTable thead tr th, table.dataTable tbody tr td').css('border-radius', '');
        $('table.dataTable thead tr th, table.dataTable tbody tr td').css('border', '0');

        $('table.dataTable').each(function () {
            $(this).find('tr').each(function () {
                $(this).css('border-bottom', '1px solid');

                $(this).find('th:visible:first').css('border-top-left-radius', '10px');
                $(this).find('th:visible:last').css('border-top-right-radius', '10px');

                $(this).find('th:visible:not(:last)').css('border-right', '1px solid');
                $(this).find('td:visible:not(:last)').css('border-right', '1px solid');
            });

            $(this).find('tr:last').css('border-bottom', '0');
            $(this).find('tr:last td:visible:first').css('border-bottom-left-radius', '10px');
            $(this).find('tr:last td:visible:last').css('border-bottom-right-radius', '10px');
        });
    }

    function changeHeader() {
        if (i == 0) {
            $(".main-logo").removeClass("animate__fadeInDown");
            $(".main-logo").addClass("animate__fadeOut");

            $(".logged-panel").show();
            $(".logged-panel").removeClass("animate__fadeOut");
            $(".logged-panel").addClass("animate__fadeInDown");
            i = 1;
        } else {
            $(".main-logo").removeClass("animate__fadeOut");
            $(".main-logo").addClass("animate__fadeInDown");

            $(".logged-panel").removeClass("animate__fadeInDown");
            $(".logged-panel").addClass("animate__fadeOut");
            i = 0;
        }
    }
</script>
"""
