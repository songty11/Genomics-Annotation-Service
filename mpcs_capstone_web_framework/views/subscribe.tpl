%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
	<div class="page-header">
		<h2>Subscribe</h2>
	</div>
	
	%if alert:
	    <div class="alert alert-success">
	      <strong>Thanks for subscribing!</strong><br />
	    </div>
	%else:
	    %if invalid:
		<p>Invalid credit card, please re-enter your credit card details.</p><br />
		%else:
			<p>You are subscribing to the GAS Premium plan. Please enter your credit card details to complete your subscription.</p><br />
		%end
	<div class="form-wrapper">
		    <form role="form" action="/subscribe" method="post" id="subscribe_form" name="subscribe_submit">

		        <div class="row">
			        <div class="form-group col-md-5">
		            	<label for="name">Name on credit card</label>
		                <input class="form-control input-lg required" type="text" size="20" data-stripe="name" />
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-5">
		            	<label for="email_address">Credit card number</label>
		                <input class="form-control input-lg required" type="text" size="20" data-stripe="number" />
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-4">
			            <label for="name">Credit card verification code</label>
		                <input class="form-control input-lg required" type="text" size="20" data-stripe="cvc" />
		            </div>
		        </div>

		        <div class="row">
			        <div class="form-group col-md-4">
			            <label for="password">Credit card expiration month</label>
		                <input class="form-control input-lg required" type="text" size="20" data-stripe="exp-month" />
		            </div>
		        </div>
		        <div class="row">
			        <div class="form-group col-md-4">
			            <label for="password">Credit card expiration year</label>
		                <input class="form-control input-lg required" type="text" size="20" data-stripe="exp-year" />
		            </div>
		        </div>			        		        

		        <br />
		        <div class="form-actions">
		            <input id="bill-me" class="btn btn-lg btn-primary" type="submit" value="Subscribe">
		        </div>        
		    </form>
	    </div>
	    %end

</div> <!-- container -->

%rebase('views/base', title='GAS - Subscribe')