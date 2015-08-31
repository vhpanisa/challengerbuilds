<table>
% for champ in champs:
% if champ == '429':
<tr>
	<td>{{champ}}</td><td>{{champs[champ]}}</td><td><a href='/show/{{champ}}/br'>Select</a></td>
</tr>
% end
% end
</table>