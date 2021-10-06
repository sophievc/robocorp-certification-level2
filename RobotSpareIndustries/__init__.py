from Browser.utils.data_types import ElementState, ScreenshotFileTypes, SelectAttribute
from RPA.Browser.Selenium import Selenium
import Browser

class RobotOrder( object ):

    def __init__(self):
        self.browser = Browser.Browser()

    def accept_terms( self ):
        if self.browser.get_element_state('xpath=//button[text()="Yep"]', state=ElementState.visible):
            self.browser.click('xpath=//button[text()="Yep"]')

    def open_application( self, url, env ='PROD' ):
        if env == 'PROD':
            self.browser.new_page(url=url)
        else:
            self.browser.open_browser(url=url)
        self.browser.wait_for_elements_state('xpath=//*[text()="RobotSpareBin Industries Inc."]', state=ElementState.visible)
        
    def close_page( self ):
        self.browser.close_page()

    def close_browser( self ):
        self.browser.close_browser()

    def new_order( self, head, body, legs, address):
        # Head
        self.browser.select_options_by('id=head', SelectAttribute['index'], head)

        # Body
        self.browser.click('id=id-body-{0}'.format(body))

        # Legs
        legs_id = self.browser.get_attribute('xpath=//label[text()="3. Legs:"]', 'for')
        self.browser.type_text('xpath=//input[@id={0}]'.format(legs_id), legs)

        #Address
        self.browser.type_text('id=address', address)

    def preview( self ):
        self.browser.click('id=preview')

    def order( self ):
        self.browser.click('id=order')
    
    def get_receipt( self ):
        self.browser.wait_for_elements_state('id=receipt', state=ElementState.visible)
        receipt = self.browser.get_text('id=receipt')
        
        return receipt

    def get_receipt_as_html( self ):
        receipt = None
        if self.browser.get_element_state('id=receipt'):
            receipt = self.browser.get_property(selector='id=receipt', property='innerHTML')
        elif self.browser.get_element_state('xpath=//div[@class="alert alert-danger"]'):
            message = self.browser.get_text('xpath=//div[@class="alert alert-danger"]')
            raise Exception(message)
        else:
            raise Exception("Unable to get receipt.")
        
        return receipt

    def download_robot_preview( self, path ):
        self.browser.wait_for_elements_state('id=robot-preview-image', state=ElementState.visible)
        self.browser.take_screenshot(filename=path, selector='id=robot-preview-image', fullPage=True, fileType=ScreenshotFileTypes.png)


    def order_another_robot(self ):
        self.browser.click('id=order-another')
        