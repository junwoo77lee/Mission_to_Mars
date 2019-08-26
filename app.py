from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import scrape_mars

#create instance of Flask app
app = Flask(__name__)

# Use PyMongo to establish Mongo connection
mongo = PyMongo(app, uri="mongodb://localhost:27017/mars_app")

@app.route('/')
def home():
    # Find a record
    mars_info = mongo.db.mars.find_one()

    return render_template('index.html', mars=mars_info,
                           mars_comp=[mars_info.get('comparison')],
                           facts=[mars_info.get('mars_facts')]
                           )


# create route that run scrape function
@app.route('/scrape')
def scrape():

    mars = mongo.db.mars

    # Run the scrape function to store info into a variable
    mars_data = scrape_mars.scrape() # a python dictionary

    # Update the Mongo database
    mars.update({}, mars_data, upsert=True)

    # Redirect back to home page
    return redirect('/', code=302)


if __name__ == '__main__':
    app.run(debug=True)
