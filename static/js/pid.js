var app = angular.module('pid', ["ngFileUpload"]);

app.controller("pid", ["$scope", "$http", "Upload", function ($scope, $http, Upload) {
    $scope.$watch('file', function () {
        console.log($scope.file);
         if ($scope.file && $scope.file !== null) {
             $scope.upload($scope.file);
        }
    });

    $http.get("/classes").success(function (response) {
        $scope.classes = response;
    });


    $scope.upload = function (file) {
        $scope.results = null;
        $scope.error = null;
        $scope.loading = true;
        Upload.upload({
            url: '/identify',
            data: {
                file: file
            }
        }).then(function (response) {
            $scope.results = [];
            $scope.loading = false;
            if (response.data.error){
                $scope.error = response.data.error;
            }else {
                angular.forEach(response.data, function (prob, cls) {
                    $scope.results.push({class: cls, probability: prob});
                });
            }
        });
    };
}]);