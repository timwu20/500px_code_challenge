var gulp = require('gulp'),
    less = require('gulp-less'),
    autoprefix = require('gulp-autoprefixer'),
    livereload = require('gulp-livereload'),
    watch = require('gulp-watch'),
 	sourcemaps = require('gulp-sourcemaps');
    LessPluginCleanCSS = require('less-plugin-clean-css'),
    cleancss = new LessPluginCleanCSS({ advanced: true });


gulp.task('less', function() {
	gulp.src('less/*.less')
		.pipe(sourcemaps.init())
		.pipe(less({
			plugins: [cleancss]
		}))
		.pipe(autoprefix('last 2 version', 'ie 8', 'ie 9'))
		.pipe(sourcemaps.write())
		.pipe(gulp.dest('css'))
		.pipe(livereload());
});

gulp.task('watch', function() {
  livereload.listen();
  gulp.watch('less/*.less', ['less']);
  gulp.watch('../templates/**').on('change', livereload.changed);
});