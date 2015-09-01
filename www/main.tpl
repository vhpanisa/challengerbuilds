<!DOCTYPE html>
<html>
	<head>
		<link rel="stylesheet" href="champion.css">
		<link href='https://fonts.googleapis.com/css?family=Roboto:100,400' rel='stylesheet' type='text/css'>
		<meta name="viewport" content="width=device-width">
	</head>

	

	<body>

		<h1 class = "txt" id = "inst">
		Select your desired champion to main and become a challenjour.
		</h1>

		<select class = "txt" id = "champion">
			<option value="0">Champion</option>
			% for champ in champs:
			<option value="{{champ}}">{{champs[champ]}}</option>
			% end
		</select>

		<select class = "txt" id = "region">
			<option value="region">All Regions</option>
		</select>

		<div>
			<a href = "#">
				<div class = "txt" id = "btn" onclick="window.location.href = '/getbuild/'+ document.getElementById('champion').options[document.getElementById('champion').selectedIndex].value">
					Get Build
				</div>
			</a>
		</div>

		<a href = "#">
			<div class = "nav" id = "left">
				◀
			</div>
		</a>

		<a href = "#">
			<div class = "nav" id = "right">
				▶
			</div>
		</a>

		<div class = "shad2"></div>

		<div class = "text" id = "shadow"></div>
	</body>
</html>