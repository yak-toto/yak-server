<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Sign Up</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidSignup">
        Name already exists.
      </div>

      <form v-on:submit.prevent="signup">
        <div class="field control">
          <label class="label" for="name">Name</label>
          <input type="text" class="input is-large" id="name" placeholder="Name" v-model="form.name">
        </div>

        <div class="field control">
          <label class="label" for="password">Password</label>
          <input type="password" class="input is-large" placeholder="Password" v-model="form.password">
        </div>

        <button class="button is-block is-info is-large is-fullwidth">Sign Up</button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'SignupComponent',
  data() {
    return {
      form: {
        name: '',
        password: '',
      },
      invalidSignup: false,
    };
  },
  methods: {
    signup() {
      const path = 'http://localhost:5000/signup';

      axios.post(path, this.form)
        .then(() => {
          this.invalidSignup = false;
          this.$router.push('/login');
        })
        .catch((error) => {
          if (error.response) {
            if (error.response.status === 409) {
              this.invalidSignup = true;
            }
          }
        });
    },
  },
};
</script>
