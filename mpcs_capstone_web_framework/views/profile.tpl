%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
        <div class="page-header">
                <h2>My Account</h2>
        </div>
        <div>
        <br>
        <strong>Full Name:</strong>
        {{auth.current_user.description}}
        <br>
        <strong>Username:</strong>
        {{auth.current_user.username}}
        <br>
        <strong>E-mail:</strong>
        {{auth.current_user.email_addr}}
        <br>
        <strong>Subscription Level:</strong>
        %if auth.current_user.role == "free_user":
        Free
        <a href = "/subscribe">(upgrade to Premium)</a>
        %else:
        Premium
        %end


</div> <!-- container -->

%rebase('views/base', title='My Account')