document.getElementById('linkButton').onclick = function() {
  fetch('/create_link_token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      access_token: 'access-production-4eb30634-4028-4498-930f-d1b0a68a92a2', // Replace with the actual access token
    }),
  })
  .then(response => response.json())
  .then(data => {
    const handler = Plaid.create({
      token: data.link_token, // Use the generated link token
      onSuccess: (public_token, metadata) => {
        // Send the public_token to your server
        fetch('/exchange_public_token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            public_token: public_token,
          }),
        });
      },
      onExit: (err, metadata) => {
        // Handle the case where your user exits Link
        if (err != null) {
          // The user encountered a Plaid API error prior to exiting.
          console.error(err);
        }
        // metadata contains information about the user's exit, which can be used for debugging.
      },
    });

    handler.open();
  });
};
