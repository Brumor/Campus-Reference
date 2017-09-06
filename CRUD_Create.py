from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)

session = DBSession()

myFirstRestaurant = Restaurant(name = "Pizza Palace")

session.add(myFirstRestaurant)
session.commit()

restaurants = session.query(Restaurant).filter_by(id = 1)

for i in restaurants:
	print i.name

cheesepizza = MenuItem (name="Cheese Pizza", description="Pizza with cheese", course = "Entree", price = "$8.99", restaurant = myFirstRestaurant)



