$(document).ready(function () {
    $('.payWithRazorpay').click(function (e) {
        e.preventDefault();
        console.log("Pay with Razorpay button clicked!");
        var addressId = $("input[name='address_id']:checked").val();
        var isExistingAddress = addressId !== undefined;

        var formData = {
            'fname': $("[name='fname']").val(),
            'lname': $("[name='lname']").val(),
            'country': $("[name='country']").val(),
            'address': $("[name='address']").val(),
            'city': $("[name='city']").val(),
            'state': $("[name='state']").val(),
            'pincode': $("[name='pincode']").val(),
            'phone': $("[name='phone']").val(),
            'email': $("[name='email']").val(),
            'total_price': $("[name='total_price']").val(),
            'csrfmiddlewaretoken': $("[name='csrfmiddlewaretoken']").val(),
            'payment_mode': 'paid by razorpay',
        };

        // If an existing address is selected, no need to perform validation
        if (!isExistingAddress) {
            if (
                formData['fname'] === "" ||
                formData['lname'] === "" ||
                formData['country'] === "" ||
                formData['address'] === "" ||
                formData['city'] === "" ||
                formData['state'] === "" ||
                formData['pincode'] === "" ||
                formData['phone'] === "" ||
                formData['email'] === ""
            ) {
                Swal.fire({
                    icon: 'error',
                    title: 'Add new address',
                    text: 'Please Enter your address. Fields cannot be empty!',
                });
                return false;
            }
            if (!/^[a-zA-Z]+$/.test(formData['fname'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid First Name',
                    text: 'First name should only contain alphabetic characters.',
                });
                return false;
            }
            
            if (!/^[a-zA-Z]+$/.test(formData['lname'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Last Name',
                    text: 'Last name should only contain alphabetic characters.',
                });
                return false;
            }
            
            if (!/^[a-zA-Z]+$/.test(formData['country'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Country Name',
                    text: 'Please enter your Country name.',
                });
                return false;
            }
            
            if (!/^[a-zA-Z]+$/.test(formData['city'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid City Name',
                    text: 'Please enter your city name.',
                });
                return false;
            }
            
            if (!/^[a-zA-Z]+$/.test(formData['state'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid State Name',
                    text: 'Please enter your state name.',
                });
                return false;
            }
            
            // if (formData['phone'] <= 0 || formData['phone'].length !== 10 || !/^\d+$/.test(formData['phone'])) {
            //     Swal.fire({
            //         icon: 'error',
            //         title: 'Invalid Phone Number',
            //         text: 'Please enter a valid 10-digit numeric phone number.',
            //     });
            //     return false;
            // }

            if (
                formData['phone'].length !== 10 ||
                !/^[6-9]\d{9}$/.test(formData['phone']) ||
                ['0000000000', '1111111111', '2222222222'].includes(formData['phone'])
            ) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Phone Number',
                    text: 'Please enter a valid 10-digit mobile number',
                });
                return false;
            }
            
            if (formData['pincode'] <= 0 || formData['pincode'].length !== 6 || !/^\d+$/.test(formData['pincode'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Pincode',
                    text: 'Please enter a valid pincode.',
                });
                return false;
            }
            
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData['email'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Email Address',
                    text: 'Please enter a valid email address.',
                });
                return false;
            }
            
            if (/^\d+$/.test(formData['address'])) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Address',
                    text: 'Please enter a valid address, not just numeric digits.',
                });
                return false;
            }
        }

        var options = {
            key: "rzp_test_W8KgTDkjH3fB0r",
            amount: formData['total_price'] * 100,
            currency: "INR",
            name: "Kickoff",
            description: "Thank you for buying from us",
            image: "/user/images/icons/logo.png",
            handler: function (response) {
                // alert(response.razorpay_payment_id);

                // Add hidden input fields with Razorpay response data
                $("<input>").attr({
                    type: "hidden",
                    name: "payment_mode",
                    value: "paid by razorpay"
                }).appendTo("#razorpay-form");

                $("<input>").attr({
                    type: "hidden",
                    name: "payment_id",
                    value: response.razorpay_payment_id
                }).appendTo("#razorpay-form");

                // Update form data based on the user's choice (existing or new address)
                for (var key in formData) {
                    if (formData.hasOwnProperty(key)) {
                        $("<input>").attr({
                            type: "hidden",
                            name: key,
                            value: formData[key]
                        }).appendTo("#razorpay-form");
                    }
                }

                // Submit the form
                $("#razorpay-form").submit();
            },
            prefill: {
                name: formData['fname'] + " " + formData['lname'],
                email: formData['email'],
                contact: formData['phone']
            },
            theme: {
                color: "#c96",
            },
        };

        var rzp1 = new Razorpay(options);
        rzp1.open();
        
    });
   
});


