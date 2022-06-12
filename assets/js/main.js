/*
 * Main Javascript file for buggy_race_server.
 *
 * This file bundles all of your javascript together using webpack.
 */

// JavaScript modules
require('jquery');
require('popper.js');
require('bootstrap');

require.context(
  '../img', // context folder
  true, // include subdirectories
  /.*/, // RegExp
);

// Your own code
require('./plugins.js');
require('./script.js');
