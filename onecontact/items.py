# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OnecontactItem(scrapy.Item):
    
    #-------------------------------------------
    #campos para uso interno
    #-------------------------------------------
    cod_anuncio = scrapy.Field()
    name = scrapy.Field()

    url_anuncio = scrapy.Field()
    url_imgs = scrapy.Field()

    #------------------------------------
    #alguns campos_adicionais parseados
    #------------------------------------
    contact_phone = scrapy.Field()
    contact_name = scrapy.Field()
    announcer = scrapy.Field()
    announcer_site = scrapy.Field()

    viewing_phone_number = scrapy.Field()
    viewing_desc = scrapy.Field()

    #------------------------------------
    #description
    #------------------------------------
    description = scrapy.Field()

    #---------------------------------------
    #general
    #---------------------------------------
    title = scrapy.Field()
    type_of_service = scrapy.Field() #adicionar
    type_of_object = scrapy.Field() #adicionar
    type_of_transaction = scrapy.Field()    # rent | buy
    nature_of_property = scrapy.Field() # residential | commercial 
    type_of_property = scrapy.Field()   
    price = scrapy.Field()
    charges = scrapy.Field()
    available_date = scrapy.Field()

    #campos qty number
    rooms_qty = scrapy.Field()
    bedrooms_qty = scrapy.Field()
    toilets_qty = scrapy.Field()
    bathrooms_qty = scrapy.Field()
    floor_qty = scrapy.Field()

    showers_qty = scrapy.Field() # adicionar
    bathtubs_qty = scrapy.Field() # adicionar
    wc_qty = scrapy.Field() # adicionar
    suite_qty = scrapy.Field() # adicionar
    vacancy_qty = scrapy.Field() # adicionar
    floor_number = scrapy.Field() # adicionar
    kitchens_qty = scrapy.Field() # adicionar
    livingrooms_qty = scrapy.Field() # adicionar
    vacancy_price = scrapy.Field() # adicionar

    surface_outer = scrapy.Field()
    surface_inner = scrapy.Field()

    #tipos: rent | owner | professional
    type_of_announcer = scrapy.Field()

    features = scrapy.Field() # lista campos que não foram parseados

    #--------------------------------------------
    #address - string campo
    #--------------------------------------------
    address = scrapy.Field()
    street_number = scrapy.Field() #address_number?
    route = scrapy.Field()
    complement =  scrapy.Field()
    neighborhood = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    country = scrapy.Field()
    postal_code = scrapy.Field()
    
    #---------------------------------------------------
    #required characteristics 
    #---------------------------------------------------
    '''
    arranged_kitchen = scrapy.Field()   #yes no not_included
    balcony = scrapy.Field()    #yes no not_included
    basement = scrapy.Field()   #yes no not_included
    elevator = scrapy.Field()   #yes no not_included 
    equipped_kitchen = scrapy.Field()   #yes no not_included
    external_area = scrapy.Field()  #yes no not_included on_demand
    furniture = scrapy.Field()  #yes no not_included
    garage = scrapy.Field() #yes no not_indicated on_demand
    ground_floor = scrapy.Field()   #yes no not_indicated
    handicap_access = scrapy.Field()    #yes no not_indicated
    parking = scrapy.Field()    #yes no not_indicated on_demand
    penthouse = scrapy.Field()  #yes no not_indicated
    private_garden = scrapy.Field() #yes no not_indicated
    superior_floor = scrapy.Field() #yes no not_indicated
    terrace = scrapy.Field()    #yes no not_indicated
    veranda = scrapy.Field()    #yes no not_indicated
    yard = scrapy.Field()   #yes no not_indicated

    #----------------------------------------------------------
    #optional characteristics - null ou 1 (pode ser num array)
    #----------------------------------------------------------

    antique_flooring = scrapy.Field()
    cuisine_habitable = scrapy.Field()
    dishwasher = scrapy.Field()
    dishwasher_location = scrapy.Field()
    dryer_machine = scrapy.Field()
    fireplace = scrapy.Field()
    high_ceilings = scrapy.Field()
    nice_view = scrapy.Field()
    opened_kitchen = scrapy.Field()
    washing_machine = scrapy.Field()
    washing_machine_location = scrapy.Field()

    #architecture characteristic - null ou 1 (pode ser um array)

    new_building = scrapy.Field()
    old_architecture = scrapy.Field()
    prestigious = scrapy.Field()
    standing = scrapy.Field()
    the_70 = scrapy.Field()

    #neighborhood - null ou 1 (pode ser um array)

    airport = scrapy.Field()
    commerce = scrapy.Field()
    downtown = scrapy.Field()
    lake = scrapy.Field()
    metro = scrapy.Field()
    organisations = scrapy.Field()
    public_transportation = scrapy.Field()
    schools = scrapy.Field()
    super_marche = scrapy.Field()   #supermercado
    train_station = scrapy.Field()
    '''
    