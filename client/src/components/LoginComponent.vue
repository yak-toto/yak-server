<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Login</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidLogin">
        Please check your login details and try again.
      </div>

      <form v-on:submit.prevent="login">
        <div class="field control">
          <label class="label" for="name">Name</label>
          <input type="text" class="input is-large" id="name" name="name" placeholder="name" v-model="request_body.name" />
        </div>

        <div class="field control">
          <label class="label" for="password">Password</label>
          <input type="password" class="input is-large" name="password" placeholder="password"
            v-model="request_body.password" />
        </div>

        <div class="field control">
          <label class="label">
            <input type="checkbox" class="checkbox" name="remember" v-model="request_body.remember" />
            Remember me
          </label>
        </div>
        <button class="button is-block is-info is-large is-fullwidth">Login</button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LoginComponent',
  data() {
    return {
      request_body: {
        name: '',
        password: '',
        remember: false,
      },
      invalidLogin: false,
    };
  },
  methods: {
    login() {
      const path = 'http://localhost:5000/login';

      axios.post(path, this.request_body)
        .then(() => {
          this.invalidLogin = false;
          this.$router.push('/groups/A');
        })
        .catch((error) => {
          if (error.response) {
            if (error.response.status === 404) {
              this.invalidLogin = true;
            }
          }
        });
    },
  },
};
</script>
