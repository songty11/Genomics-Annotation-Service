%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
        <div class="page-header">
                <h2>My Annotations</h2>
        </div>
        <div>
         <a class="btn btn-lg btn-primary" href="/annotate">Request New Annotation</a>
        </div>
        <br>
        <table class="table table-striped">
        <th>Request ID</th>
        <th>Request Time</th>
        <th>VCF File Name</th>
        <th>Status</th>
        %for i in item:
        <tr>
     <td><a href="/annotations/{{i['job_id']}}">{{i['job_id']}}</td></a>
     <td>{{i["submit_time"]}}</td>
     <td>{{i["input_file_name"]}}</td>
     <td>{{i["job_status"]}}</td>
     </tr>
        %end
     </table>


</div> <!-- container -->

%rebase('views/base', title='My Annotations')