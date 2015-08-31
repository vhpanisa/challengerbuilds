<h1>{{champ}}</h1>
% for build in builds:
<table>
<tr>
	% for item in build:
	% if item in items:
	<td>{{items[item]}}</td>
	% end
	% end
</tr>
</table>
% end