#TVme

TVme is a social cataloging webapp that helps users keep track of their TV shows and interact with friends about what they are watching. Users can search its database, see detailed information about each show, rate and review, and keep track of which episodes and shows they’re currently watching, want to watch, or have already seen. 

TVme is written using Python, SQLite, SQLAlchemy, Flask, Jinja, and Javascript.

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.07.02%20PM.png?raw=true "Series Page")

###Database
######(model.py)
All the TV show information is gathered using theTVDB.com API, which returns an xml document. pyQuery is used to access the xml more easily and the show information is added to the database using SQLAlchemy. TV shows are only added to the database once a user searches for and views a series.

###User Interface:
######(/templates)
Users can see their lists of shows and whether they have watched, will watch, would like to watch, or favorited a show (my_shows.html). The information is pulled from the database using AJAX. 
The search (search.html) implements theTVDB.com API to deliver search results.
On the series page (series_page.html) Jinja is used to populate the series and episode information. AJAX is used to update the watched episodes and star rating.
The episode page (episode_page.html) uses jQuery to show the spoiler section or not depending if the user has marked the episode as watched, and to update reviews.

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.07.37%20PM.png?raw=true "My Shows Page")

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.08.14%20PM.png?raw=true "Series Page")