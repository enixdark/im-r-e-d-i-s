(function(){

	var app = angular.module('app', []);
	var mainController = function ($scope,$http,$interval,$log,getHttp) {

		$scope.hello = "hello";
		var getListData = function(){
			getHttp.getListData().then(function(res){
				console.log(res.data);
			});
		}
		var voteArticle = function(data){

		}
		$scope.getListData = getListData;
		getListData();

	};

	var getHttp = function($http,$log){

		var getListData = function(){
			return $http.get('/get_list_data').then(function(res){
				return res.data
			});
		};

		var putData = function(data){
			var id = data.id.split(':')[1];
			$log.info(id);
			// $.ajax({
			// 	url: '/put_data/' + id,
			// 	type: 'PUT',
			// 	data: JSON.stringify(data),
			// 	headers: {'Content-Type': 'application/json'},
			// 	contentType: "application/json",
			// 	success: function(d) {
			// 		return JSON.stringify(data);
			// 	}
			// });
			$http.put('/put_data/' + id,data).success(function(data, status, headers, config) {
				$log.info(JSON.stringify(data));
			}).
			error(function(data, status, headers, config) {
				$log.info(JSON.stringify(data));
			});
		};

		return {
			getListData: getListData,
			putData:putData
		};
	};
	app.factory("getHttp", getHttp);
	// app.controller('MainController', MainController);
	app.controller('mainController', ['$scope','$http','$log','getHttp', function ($scope,$http,$log,getHttp) {
		$scope.listData = [];
		var getListData = function(){
			getHttp.getListData().then(function(res){
				$scope.listData  = res;
			});
		};
		var vote = function(data){

			var value = data.votes.valueOf();
			$log.info(typeof parseInt(value));
			return {
				vote_up:function(){
					data.votes = parseInt(value) + 1;
					getHttp.putData(data);
				},
				vote_down:function(){
					data.votes = parseInt(value) - 1;
				},

			};
		};

		$scope.event_vote = vote;
		getListData();


	}]);


}());
