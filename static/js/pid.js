var app = angular.module('pid', ["ngFileUpload"]);

app.controller("pid", ["$scope", "$http", "Upload", function ($scope, $http, Upload) {
    $scope.$watch('files', function () {
         if ($scope.files && $scope.files !== null && $scope.files.length > 0) {
             $scope.upload($scope.files);
        }
    });

    $http.get("/classes").success(function (response) {
        $scope.classes = response;
    });

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position){
            $scope.$apply(function(){
                $scope.lat = position.coords.latitude;
                $scope.lng = position.coords.longitude;
            });
        });
        $scope.week = (new Date()).getWeekNumber();
    }

    $scope.strategies = [
        {'id': 'fast', 'name': 'Rychle'},
        {'id': 'medium', 'name': 'Středně rychle'},
        {'id': 'slow', 'name': 'Pomalu'},
        {'id': 'extra_slow', 'name': 'Extra pomalu'}
    ];
    $scope.strategy = $scope.strategies[0];

    $scope.upload = function (files) {
        $scope.images = null;
        $scope.error = null;
        $scope.loading = true;
        Upload.upload({
            url: '/identify?strategy='+$scope.strategy.id,
            data: {
                files: files,
                lat: $scope.lat,
                lng: $scope.lng,
                week: $scope.week
            }
        }).then(function (response) {
            $scope.images = [];
            $scope.loading = false;
            if (response.data.error){
                $scope.error = response.data.error;
            }else {
                angular.forEach(response.data.images, function (image) {
                    var img = {results: [], raw_predictions: [], certainties: image.certainties};
                    angular.forEach(image.plants, function (prob, cls) {
                        img.results.push({class: cls, probability: prob});
                    });
                    angular.forEach(image.raw_predictions, function (prob, cls) {
                        img.raw_predictions.push({class: cls, probability: prob});
                    });
                    $scope.images.push(img);
                });
                $scope.suggestions = [];
                angular.forEach(response.data.suggestions, function (prob, cls) {
                    $scope.suggestions.push({class: cls, probability: prob});
                });
            }
        }, function(response){
            $scope.loading = false;
            $scope.error = "Something went wrong.";
        });
    };
}]);

Date.prototype.getWeekNumber = function(){
    var d = new Date(+this);
    d.setHours(0,0,0);
    d.setDate(d.getDate()+4-(d.getDay()||7));
    return Math.ceil((((d-new Date(d.getFullYear(),0,1))/8.64e7)+1)/7);
};