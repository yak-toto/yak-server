<template>
  <div class="column is-4 is-offset-4">
    <h3 class="title">Se connecter</h3>
    <div class="box">
      <div class="notification is-danger" v-if="invalidLogin">
        Veuillez vérifier vos identifiants et réessayer.
      </div>

      <form v-on:submit.prevent="login">
        <div class="field control">
          <label class="label" for="name">Nom</label>
          <input type="text" class="input is-large" id="name" name="name" placeholder="nom" v-model="name" />
        </div>

        <div class="field control">
          <label class="label" for="password">Mot de passe</label>
          <input type="password" class="input is-large" name="password" placeholder="mot de passe"
            v-model="password" />
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
          console.log(response);
          this.$store.commit('setJwtToken', { jwt: response.data });
          this.$store.commit('setUserName', { userName: this.name });
          this.$router.push('/groups/A');
        })
        .catch((error) => {
          console.log('Error Authenticating: ', error);
          this.invalidLogin = true;
        });
    },
  },
};
</script>
