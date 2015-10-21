/*
 *	Taras Tovchenko 8-10-15
 */

 var n3 = n3 || {};

 n3.multires = {
 	_multiresPath: null,
 	defaultLODs: [1024, 2048, 4096]

 	setup: function(LODs) {
 		if (!LODs) LODs = this.defaultLODs;
 		if (!_.isArray(LODs))
 			throw new Error('LODs must be an Array type.');

 		LODs.sort();

		var fs = cc.view.getFrameSize();
		var found = false;
 		for (var i = 0; i < LODs.length; ++i) {
 			if (fs.width <= LODs[i] && fs.height <= LODs[i]) {
 				cc.view.setDesignResolutionSize(fs.width, fs.height, cc.ResolutionPolicy.NO_BORDER);
 				this._multiresPath = LODs[i].toString();
 				found = true;
 				break;
 			}
 		}

 		if (!found) { // screen is bigger than the biggest texture
 			fs.width /= _.last(LODs);
 			fs.height /= _.last(LODs);
 			cc.director.setContentScaleFactor(1.0 / Math.max(fs.width, fs.height));
 			cc.view.setDesignResolutionSize(fs.width, fs.height, cc.ResolutionPolicy.NO_BORDER);
 			this._multiresPath = _.last(LODs).toString();
 		}

 		cc.sys.isNative && jsb.fileUtils.setSearchResolutionsOrder([this._multiresPath]);
 	},

 	makeResourcePath: function(path, useMultiResPath, useccLoaderResPath) {
 		var pathParts = path.split('/');
 		var len = pathParts.length;
 		if (len > 1 && pathParts[0] === '') --len; // if path begins from slash
 		var base = cc.path.basename(path);

 		if (len > 1) {
 			var hasMultiResPath = (pathParts[len - 2] === this._multiresPath);
 			var hasccLoaderResPath = (hasMultiResPath && len > 2 && pathParts[len - 3] === cc.loader.resPath)
 									|| (!hasMultiResPath && pathParts[len - 2] === cc.loader.resPath);

 			if (useMultiResPath) {
 				if (hasMultiResPath && hasccLoaderResPath) {
 					if (useccLoaderResPath) return path;
 					return cc.path.join(this._multiresPath, base);
 				}
 				if (hasccLoaderResPath) {
 					if (useccLoaderResPath)
 						return cc.path.join(cc.path.join(cc.path.dirname(path), this._multiresPath), base);
 					return cc.path.join(this._multiresPath, base);
 				}
 				if (hasMultiResPath)
 					return path;

 				throw new Error('Can\'t calculate a path.');
 			} else {
 				if (hasMultiResPath && hasccLoaderResPath) {
 					pathParts.splice(len - 1, 1);
 					return cc.path.join(pathParts.join('/'), base);
 				}
 				if (hasccLoaderResPath)
 					return path;

 				throw new Error('Can\'t calculate a path.');
 			}
 		} else {
 			return useMultiResPath
 				? useccLoaderResPath
 					? cc.path.join(cc.path.join(cc.loader.resPath, this._multiresPath), path)
 					: cc.path.join(this._multiresPath, path)
 				: cc.path.join(cc.loader.resPath, path);
 		}
 	}
 };