%include('views/header.tpl')
<div class="container">
	<div class="page-header">
                <h2>Log File</h2>
        </div>
	%for line in content:
	{{line}}
	<br>
	%end

<hr/>
<a href="/annotations">&larr; back to annotations list </a>

</div> <!-- container -->
%rebase('views/base', title='Log File')

