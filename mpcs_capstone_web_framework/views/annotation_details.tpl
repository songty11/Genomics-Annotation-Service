%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
        <div class="page-header">
                <h2>Annotation Details</h2>
        </div>
        <div>
        <br>
        <strong>Request ID:</strong>
        {{request_id}}
        <br>
        <strong>Request Time:</strong>
        {{request_time}}
        <br>
        <strong>VCF Input File:</strong>
        <a href={{input_url}}>{{input_file}}</a>
        <br>
        <strong>Status:</strong>
        {{status}}
        <br>
        <strong>Complete Time:</strong>
        {{complete_time}}
        </div>
        <br>
        <hr />

%if status == "COMPLETE":


 <strong>Annotated Result File:</strong>
 %if auth.current_user.role == "free_user":
 %if over_hours:
<a href = "/subscribe">upgrade to Premium for download</a>
%else:
<a href={{result_url}} >download</a>
%end
%else:
<a href={{result_url}} >download</a>
%end
 <br>
 <strong>Annotation Log File:</strong>
 <a href = "/annotations/{{request_id}}/log">download </a>
 <br>

%else:


 <strong>Annotated Result File:</strong>
 Job is still running
 <br>
 <strong>Annotation Log File:</strong>
 Job is still running
 <br>


%end
<hr/>
<a href="/annotations">&larr; back to annotations list </a>





</div> <!-- container -->

%rebase('views/base', title='My Annotations')