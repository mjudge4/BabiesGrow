(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

self.addEventListener('fetch', function (event) {
  console.log('help');
});

},{}],2:[function(require,module,exports){
"use strict";

var r = FetchEvent.prototype.respondWith;
FetchEvent.prototype.respondWith = function () {
  return new URL(this.request.url).search.endsWith("bypass-sw") ? void 0 : r.apply(this, arguments);
};

},{}]},{},[1,2])

//# sourceMappingURL=sw.js.map

/*
this.addEventListener('fetch', function(event) {
   event.respondWith(networkOrCache(event.request));
});

function networkOrCache(request) {
   return fetch(request).catch(function() {
       return fromCache(request);
   });
}

function fromCache(request) {
   return caches.open('my-cache').then(function (cache) {
       return cache.match(request).then(function (matching) {
           return matching
       });
   });
}

this.addEventListener('fetch', function(event) {
   event.respondWith(fromCache(event.request));

   event.waitUntil(addToCache(event.request));
});

function addToCache(request) {
   return caches.open('my-cache').then(function (cache) {
       return fetch(request).then(function (response) {
           return cache.put(request, response);
       });
   });
}

*/

