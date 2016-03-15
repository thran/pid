module.exports = function(grunt) {

grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
        libs: {
            src: [
                'bower_components/foundation/js/vendor/jquery.js',
                'bower_components/angular/angular.min.js',
                'bower_components/angular-animate/angular-animate.min.js',
                'bower_components/foundation/js/vendor/modernizr.js',
                'bower_components/foundation/js/foundation.min.js'
            ],
            dest: 'static/libs.min.js'
        },
        dist: {
            src: ['static/js/*.js'],
            dest: 'static/pid.js'
        }
    },
    uglify: {
        options: {
            banner: '/*! <%= pkg.name %>-libs <%= grunt.template.today("yyyy-mm-dd") %> */\n'
        },
        build: {
            src: 'static/pid.js',
            dest: 'static/pid.min.js'
        }
    },
    jshint: {
        files: ['static/js/*.js']
    },
    watch: {
        files: ['static/js/*.js', "static/css/*.css"],
        tasks: ['jshint', 'concat:dist', 'uglify:build', "cssmin"]
    },
    cssmin: {
        target: {
            files: {
                'static/pid.css': [
                    "bower_components/foundation/css/normalize.css",
                    "bower_components/foundation/css/foundation.css",
                    'static/css/*.css'
                ]
            }
        }
    }
});

    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-angular-templates');
    grunt.loadNpmTasks('grunt-contrib-copy');

    grunt.registerTask('default', ['jshint', 'concat', 'uglify:build', "cssmin"]);
};