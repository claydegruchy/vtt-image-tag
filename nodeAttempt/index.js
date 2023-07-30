/*jshint strict:false */

(function () {
    'use strict';
    // this function is strict...
}());

// Setting up our app requirements
const express = require('express');
const Server = require('http').Server;
const path = require('path');
const cors = require('cors');
const fs = require('fs');



const app = express();
app.use(cors());
const server = new Server(app);
const port = 30001;

const imagePath = "/Users/power/Downloads/"
const filePrefix = "degruchy_"
const tagSpliter = ","
const fileNameSplitter = "_"

// Setting up our port
server.listen(port, () => console.log("running on ip and address " + "http://localhost:" + port));


// allow localhost cors requests

// disable cors



const sendDefaultImage = (res) => {
    res.sendFile(path.join(__dirname, 'tests/im.png'));
}

const getFilesFromDir = (dir) => {
    const files = fs.readdirSync(dir);
    return files.filter(file => file.startsWith(filePrefix)).map(file => path.join(imagePath, file));
}


app.use((req, res, next) => {
    const ua = req.headers['user-agent'];
    const origin = req.headers.origin;
    console.log({ ua, origin });
    // add expiry
    
    next();
})

// a wildcard route
app.get('/image.jpg', (req, res) => {
    const tags = req.query.tags;
    // add image content type
    if (!tags) return sendDefaultImage(res)
    const words = tags.split(',');
    const images = getFilesFromDir(imagePath)
    // pick a random image from the directory
    const image = images[Math.floor(Math.random() * images.length)];
    res.setHeader('Cache-Control', 'public, max-age=3');
    
    res.sendFile(image);
})

// base route
app.get('/', (req, res) => {
    return sendDefaultImage(res)
});

// send redirect to base route
app.get('*', (req, res) => {
    res.redirect('/');
});


