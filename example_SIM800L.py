
# ---------------------
# SIM800L example usage
# ---------------------

from SIM800L import Modem
import json

def example_usage():
    print('Starting up...')

    # Create new modem object on the right Pins
    modem = Modem(MODEM_PWKEY_PIN    = 4,
                  MODEM_RST_PIN      = 5,
                  MODEM_POWER_ON_PIN = 23,
                  MODEM_TX_PIN       = 0,
                  MODEM_RX_PIN       = 1)

    # Initialize the modem
    modem.initialize()

    # Run some optional diagnostics
    #print('Modem info: "{}"'.format(modem.get_info()))
    #print('Network scan: "{}"'.format(modem.scan_networks()))
    #print('Current network: "{}"'.format(modem.get_current_network()))
    #print('Signal strength: "{}%"'.format(modem.get_signal_strength()*100))

    # Connect the modem
    modem.connect(apn='internet.itelcel.com', user='webgpr', pwd='webgprs2002') #leave username and password empty if your network don't require them
    print('\nModem IP address: "{}"'.format(modem.get_ip_addr()))

    # Example GET
    print('\nNow running demo http GET...')
    url = 'http://byh16n3.herokuapp.com/api/codeEvent/+526645205849'
    response = modem.http_request(url, 'GET')
    print('Response status code:', response.status_code)
    print('Response content:', response.content)

    # Example POST
    print('Now running demo https POST...')
    url  = 'http://byh16n3.herokuapp.com/api/codeEvent/new'
    data = json.dumps({"codeId":"62f05aaffcc8845454760252","picId":"NA.sim800","CoreSim":"+526645205849"})
    response = modem.http_request(url, 'POST', data, 'application/json')
    print('Response status code:', response.status_code)
    print('Response content:', response.content)

    # Disconnect Modem
    modem.disconnect()

