<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Se connecter</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidLogin">
        Veuillez vérifier vos identifiants et réessayer.
      </div>

      <form v-on:submit.prevent="login">
        <div class="field control">
          <label class="label" for="pseudo">
            Pseudo
            <input type="text" class="input is-large" id="pseudo" name="pseudo"
              placeholder="pseudo" v-model="name" />
          </label>
        </div>

        <div class="field control">
          <label class="label" for="password">
            Mot de passe
            <input type="password" class="input is-large" name="password"
              placeholder="mot de passe" v-model="password" />
          </label>
        </div>

        <button class="button is-block is-info is-large is-fullwidth">Se connecter</button>
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
      invalidLogin: false,
    };
  },
  methods: {
    login() {
      this.$store.dispatch('login', { name: this.name, password: this.password })
        .then((response) => {
          this.$store.commit({ type: 'setJwtToken', jwt: response.data.result.token });
          this.$store.commit({ type: 'setUserName', userName: response.data.result.name });
          this.$router.push('/groups/A');
        })
        .catch(() => {
          this.invalidLogin = true;
        });
    },
  },
};
</script>
