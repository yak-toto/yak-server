<template>
  <div class="columns">
    <div class="column is-2">
      <GroupNavbar />
    </div>
    <div class="column">
      <h3 class="title">Classement</h3>
      <div class="box">
        <div class="table-container">
          <table class="table is-fullwidth is-striped">
            <thead>
              <tr>
                <th>Joueur</th>
                <th>Points</th>
              </tr>
            </thead>
            <tr v-for="res in scoreBoardResource">
              <td>
                <div>{{ res["name"] }}</div>
              </td>
              <td>
                <div>{{ res["points"] }}</div>
              </td>
            </tr>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'ScoreBoardComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      scoreBoardResource: [],
    };
  },
  methods: {
    getScoreBoard() {
      this.$store.dispatch('getScoreBoard')
        .then((res) => { this.scoreBoardResource = res.data; });
    },
  },
  beforeEnter(to, from, next) {
    if (!this.$store.getters.isAuthenticated) {
      this.$store.dispatch('logout');
      next('/login');
    } else {
      next();
    }
  },
  created() {
    this.getScoreBoard();
  },
};

</script>
