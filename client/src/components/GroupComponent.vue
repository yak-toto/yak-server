<template>
  <GroupNavbar />
  <hr>
  <div class="column is-8 is-offset-2">
    <h3 class="title">Groupe {{ $route.params.group_name }}</h3>
    <div class="box">
      <form v-on:submit.prevent="postGroup">
        <div class="table-container">
          <table class="table is-fullwidth is-striped">
            <tr v-for="match in group_resource">
              <td>{{ match[0]["team"] }}</td>
              <td><input class="input is-small" type="number" v-model="match[0]['score']"></td>
              <td><input class="input is-small" type="number" v-model="match[1]['score']"></td>
              <td>{{ match[1]["team"] }}</td>
            </tr>
          </table>
        </div>
        <div>
          <button class="button is-dark">Submit</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'GroupComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      group_resource: [],
    };
  },
  methods: {
    getGroup() {
      const path = `http://localhost:5000/groups/${this.$route.params.group_name}`;

      axios.get(path)
        .then((res) => {
          this.group_resource = res.data;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    postGroup() {
      const path = `http://localhost:5000/groups/${this.$route.params.group_name}`;

      console.log(this.group_resource);

      axios.post(path, this.group_resource)
        .then(() => {

        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        })
    },
  },
  created() {
    this.$watch(
      () => this.$route.params,
      () => {
        this.getGroup();
      },
      { immediate: true },
    );
  },
};

</script>
