var app = angular.module('pid', ["ngFileUpload"]);

app.controller("pid", ["$scope", "$http", "Upload", function ($scope, $http, Upload) {
    $scope.$watch('file', function () {
         if ($scope.file && $scope.file !== null) {
             $scope.upload($scope.file);
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


    $scope.upload = function (file) {
        $scope.results = null;
        $scope.error = null;
        $scope.loading = true;
        Upload.upload({
            url: '/identify',
            data: {
                file: file,
                lat: $scope.lat,
                lng: $scope.lng,
                week: $scope.week
            }
        }).then(function (response) {
            $scope.results = [];
            $scope.loading = false;
            if (response.data.error){
                $scope.error = response.data.error;
            }else {
                angular.forEach(response.data.plants, function (prob, cls) {
                    $scope.results.push({class: cls, probability: prob});
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