<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Login</h3>
    <div class="box">
      <form method="POST" action="/login">
        <div class="field">
          <label class="control">
            <input class="input is-large" type="name"
              name="name" placeholder="Your Name"/>
          </label>
        </div>

        <div class="field">
          <label class="control">
            <input class="input is-large" type="password"
              name="password" placeholder="Your Password"/>
          </label>
        </div>
        <div class="field">
          <label class="checkbox">
            <input type="checkbox">
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
      msg: 'Hello!',
    };
  },
  methods: {

  },
};
</script>
