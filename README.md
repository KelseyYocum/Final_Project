#TVme

TVme is a social cataloging site for TV shows— a place to keep track of TV shows and interact with friends. TV talk these days often ends up on Twitter or Facebook where it’s lost amongst all the other updates and spoilers abound. TVme keeps your TV conversation in one place and a way to keep track of all your TV shows, not just the ones in your Netflix or Hulu queue.

TVme is written using Python, SQLite, SQLAlchemy, Flask, Jinja, and Javascript.

The My Shows page (**my_shows.html**) is the main page for the user. This is where the user can see all the shows they are keeping track of and whether they are currently watching the show, watched it previously, want to watch it, or if it is a favorite. This information is pulled from the database (**model.py**) using AJAX.

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.07.37%20PM.png?raw=true "My Shows Page")

Once a series is clicked, the user is directed to the series page (**series_page.html**). All routes are handled using Flask as the web framework . Here you can see more information about the series, the various seasons, episodes, and episode information. You can rate the series and change its status (currently watching, watched, to-watch). You can also click whether or not you’ve watched individual episodes, which changes the series progress bar. The season tables and episode information is hidden and shown using jQuery.

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.07.02%20PM.png?raw=true "Series Page") 

The series information originates from thetvdb.com API as XML, parsed and accessed using PyQuery, and then stored in the database using SQLAlchemy. Series can be searched for in the menu bar using the built in search from the API, allowing users to access thousands of shows. Series are only added to the database once a searched-for series is clicked on and the user is taken to its series page.

Users can also click on “more information” under a specific episode description, directing them to an episode page (**episode_page.html**). Here, more information about the episode is provided and users can write (or edit) a review for the episode and see friends’ reviews. If the episode has not been clicked as “watched,” friends’ reviews are hidden under a “spoil me” button so that users are not accidently spoiled by friends’ reviews.

![alt text](https://github.com/KelseyYocum/Hackbright_Project/blob/master/static/img/Screen%20Shot%202013-12-03%20at%2012.08.14%20PM.png?raw=true "Episode Page") 

A great deal of thought was given to the UX of TVme. Everything was wireframed ahead of time and the interactions made as intuitive as possible.
