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
          <input type="text" class="input is-large" id="name" name="name" placeholder="name" v-model="name" />
        </div>

        <div class="field control">
          <label class="label" for="password">Password</label>
          <input type="password" class="input is-large" name="password" placeholder="password"
            v-model="password" />
        </div>

        <div class="field control">
          <label class="label">
            <input type="checkbox" class="checkbox" name="remember" v-model="remember" />
            Remember me
          </label>
        </div>
        <button class="button is-block is-info is-large is-fullwidth">Login</button>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginComponent',
  data() {
    return {
      name: '',
      password: '',
      remember: false,
      invalidLogin: false,
    };
  },
  methods: {
    login() {
      this.$store.dispatch('login', { name: this.name, password: this.password })
        .then(() => this.$router.push('/groups/A'))
    },
  },
};
</script>
