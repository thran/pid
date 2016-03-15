var app = angular.module('pid', ["ngFileUpload"]);

app.controller("pid", ["$scope", "$http", "Upload", function ($scope, $http, Upload) {
    $scope.$watch('file', function () {
         if ($scope.file && $scope.file !== null) {
             $scope.upload($scope.file);
        }
    });

    $scope.upload = function (file) {
        Upload.upload({
            url: '/identify',
            data: {
                file: file
            }
        }).then(function (response) {
            $scope.results = [];
            angular.forEach(response.data, function (prob, cls) {
                $scope.results.push({class: cls, probability: prob});
            });
        });
    };
}]);