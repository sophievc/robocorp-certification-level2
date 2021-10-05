from typing import cast
from RPA.Browser.Selenium import Selenium
import time

class RobotOrder( object ):

    def __init__(self):
        self.browser = Selenium()

    def accept_terms( self ):
        if self.browser.is_element_visible('xpath://button[text()="Yep"]'):
            self.browser.click_button('xpath://button[text()="Yep"]')

    def open_application( self, url ):
        self.browser.open_available_browser(url)
        self.browser.wait_until_element_is_enabled('xpath://*[text()="RobotSpareBin Industries Inc."]')
        
    def close_application( self ):
        self.browser.close_browser()

    def new_order( self, head, body, legs, address):
        # Head
        self.browser.select_from_list_by_index('id:head', head)

        # Body
        self.browser.click_element('id:id-body-{0}'.format(body))

        # Legs
        legs_id = self.browser.get_element_attribute('xpath://label[text()="3. Legs:"]', 'for')
        self.browser.input_text('xpath://input[@id={0}]'.format(legs_id), legs)

        #Address
        self.browser.input_text('id:address', address)

    def preview( self ):
        self.browser.click_button('id:preview')

    def order( self ):
        self.browser.click_button('id:order')
    
    def get_receipt( self ):
        self.browser.wait_until_element_is_visible('id:receipt')
        receipt = self.browser.get_text('id:receipt')
        
        return receipt

    def get_receipt_as_html( self ):
        self.browser.wait_until_element_is_visible('id:receipt')
        receipt = self.browser.get_element_attribute('id:receipt', 'innerHTML')

        return receipt

    def download_robot_preview( self, path ):
        self.browser.wait_until_element_is_visible('id:robot-preview-image')
        self.browser.capture_element_screenshot('id:robot-preview-image', path)


    def order_another_robot(self ):
        self.browser.click_button('id:order-another')
        self.browser.wait_until_element_is_not_visible('id:order-another')
        

if __name__ == '__main__':
    order = RobotOrder()
    order.open_application()
    order.accept_terms()
    order.new_order(head = "1", body= "2", legs="3", address='Address 123')
    order.preview()
    order.order()
    order.get_receipt()
    order.order_another_robot()
    order.accept_terms()
