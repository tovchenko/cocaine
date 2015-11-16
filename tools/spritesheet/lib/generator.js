var exec = require('platform-command').exec;
var fs = require('fs');
var Mustache = require('mustache');
var async = require('async');
var os = require('os');
var path = require('path');

var packing = require('./packing/packing.js');
var sorter = require('./sorter/sorter.js');
var imagetools = __dirname + '/../imageCombine.app/Contents/MacOS/imageCombine';

/**
 * Generate temporary trimmed image files
 * @param {string[]} files
 * @param {object} options
 * @param {boolean} options.trim is trimming enabled
 * @param callback
 */
exports.trimImages = function (files, options, callback) {
	var scale = options.scale ? ' -s ' + options.scale : '';
	var trim = options.trim ?  ' -t ' + (options.fuzz ? 'all-alpha ' : 'max-alpha ') : '';
	var filePaths = files.map(function(file) {
		return '"' + file.path + '"';
	});

	exec(imagetools + scale + trim + ' -d "' + os.tmpDir() + '" ' + filePaths.join(' '), function(err, stdout) {
		if (err) return callback(err);

		var sizes = stdout.split('\n');
		sizes = sizes.splice(0, sizes.length - 1);
		sizes.forEach(function (item, i) {
			var size = item.match(/ ([0-9]+)x([0-9]+) /);
			files[i].width = parseInt(size[1], 10) + options.padding * 2;
			files[i].height = parseInt(size[2], 10) + options.padding * 2;
			files[i].area = files[i].width * files[i].height;
			files[i].trimmed = false;

			if (options.trim) {
				var rect = item.match(/ ([0-9]+)x([0-9]+)[\+\-]([0-9]+)[\+\-]([0-9]+)/);
				files[i].trim = {};
				files[i].trim.x = parseInt(rect[3], 10);
				files[i].trim.y = parseInt(rect[4], 10);
				files[i].trim.width = parseInt(rect[1], 10);
				files[i].trim.height = parseInt(rect[2], 10);

				files[i].trimmed = (files[i].trim.width !== files[i].width - options.padding * 2 || files[i].trim.height !== files[i].height - options.padding * 2);
			}
		});
		
		files.forEach(function(file) {
			file.originalPath = file.path;
			file.path = path.join(os.tmpDir(), path.basename(file.originalPath, path.extname(file.originalPath)) + '.png');
		});

		callback(null, files);
	});
};

/**
 * Determines texture size using selected algorithm
 * @param {object[]} files
 * @param {object} options
 * @param {object} options.algorithm (growing-binpacking, binpacking, vertical, horizontal)
 * @param {object} options.square canvas width and height should be equal
 * @param {object} options.powerOfTwo canvas width and height should be power of two
 * @param {function} callback
 */
exports.determineCanvasSize = function (files, options, callback) {
	files.forEach(function(item) {
		item.w = item.trimmed ? item.trim.width : item.width;
		item.h = item.trimmed ? item.trim.height : item.height;
	});

	// sort files based on the choosen options.sort method
	sorter.run(options.sort, files);

	packing.pack(options.algorithm, files, options);

	if (options.square) {
		options.width = options.height = Math.max(options.width, options.height);
	}

	if (options.powerOfTwo) {
		options.width = roundToPowerOfTwo(options.width);
		options.height = roundToPowerOfTwo(options.height);
	}

	callback(null, options);
};

/**
 * generates texture data file
 * @param {object[]} files
 * @param {object} options
 * @param {string} options.path path to image file
 * @param {function} callback
 */
exports.generateImage = function (files, options, callback) {
	var command = [imagetools + ' -w ' + options.width + ' -h ' + options.height + ' -a ' + ' -d ' + '"' + options.path + '/' + options.name + '.png" '];
	files.forEach(function(file) {
		command.push('"' + file.path + '" ' + (file.x + options.padding) + ' ' + (file.y + options.padding));
	});
	exec(command.join(' '), function (err) {
		if (err) return callback(err);

		unlinkTempFiles(files);
		callback(null);
	});
};

function unlinkTempFiles(files) {
	files.forEach(function (file) {
		if (file.originalPath && file.originalPath !== file.path) {
			fs.unlinkSync(file.path.replace(/\\ /g, ' '));
		}
	});
}

/**
 * generates texture data file
 * @param {object[]} files
 * @param {object} options
 * @param {string} options.path path to data file
 * @param {string} options.dataFile data file name
 * @param {function} callback
 */
exports.generateData = function (files, options, callback) {
	var formats = (Array.isArray(options.customFormat) ? options.customFormat : [options.customFormat]).concat(Array.isArray(options.format) ? options.format : [options.format]);
	formats.forEach(function(format, i){
		if (!format) return;
		var path = typeof format === 'string' ? format : __dirname + '/../templates/' + format.template;
		var templateContent = fs.readFileSync(path, 'utf-8');

		// sort files based on the choosen options.sort method
		sorter.run(options.sort, files);

		options.files = files;
		options.files[options.files.length - 1].isLast = true;
		options.files.forEach(function (item, i) {
			item.width  -= options.padding * 2;
			item.height -= options.padding * 2;
			item.x += options.padding;
			item.y += options.padding;

			item.index = i;
			if (item.trim) {
				item.trim.frameX = -item.trim.x;
				item.trim.frameY = -item.trim.y;
				item.trim.offsetX = Math.floor(Math.abs(item.trim.x + item.width / 2 - item.trim.width / 2));
				item.trim.offsetY = Math.floor(Math.abs(item.trim.y + item.height / 2 - item.trim.height / 2));
			}
			item.cssName = item.name || "";
			item.cssName = item.cssName.replace("_hover", ":hover");
			item.cssName = item.cssName.replace("_active", ":active");
		});

		var result = Mustache.render(templateContent, options);
		function findPriority(property) {
			var value = options[property];
			var isArray = Array.isArray(value);
			if (isArray) {
				return i < value.length ? value[i] : format[property] || value[0];
			}
			return format[property] || value;
		}
		fs.writeFile(findPriority('path') + '/' + findPriority('name') + '.' + findPriority('extension'), result, callback);
	});
};

/**
 * Rounds a given number to to next number which is power of two
 * @param {number} value number to be rounded
 * @return {number} rounded number
 */
function roundToPowerOfTwo(value) {
	var powers = 2;
	while (value > powers) {
		powers *= 2;
	}

	return powers;
}
